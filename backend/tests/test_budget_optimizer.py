"""Unit tests for the GA budget optimizer."""

import numpy as np
import pytest

from app.agent.budget_optimizer import (
    CATEGORIES,
    GENE_MIN,
    NUM_GENES,
    BudgetGA,
    optimize_budget,
)


class TestRepair:
    def test_enforces_min_and_sums_to_one(self):
        chromosomes = np.array([
            [0.60, 0.40, 0.00, 0.00],
            [0.20, 0.20, 0.20, 0.20],
            [0.99, 0.01, 0.00, 0.00],
        ])
        repaired = BudgetGA._repair(chromosomes)
        assert np.all(repaired >= GENE_MIN - 1e-6)
        assert np.allclose(repaired.sum(axis=1), 1.0)

    def test_idempotent_on_valid_input(self):
        valid = np.array([
            [0.25, 0.35, 0.25, 0.15],
            [0.30, 0.30, 0.25, 0.15],
        ])
        valid /= valid.sum(axis=1, keepdims=True)
        repaired = BudgetGA._repair(valid)
        assert np.allclose(repaired, valid, atol=1e-4)


class TestPopulationInit:
    def test_all_chromosomes_sum_to_one(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[])
        pop = ga._initialize_population()
        assert pop.shape == (200, 4)
        assert np.allclose(pop.sum(axis=1), 1.0)
        assert np.all(pop >= GENE_MIN - 1e-6)


class TestFitness:
    def test_better_match_gives_higher_score(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[], seed=42)
        good = ga._target.copy().reshape(1, -1)
        bad = np.array([[0.50, 0.10, 0.30, 0.10]])
        combined = np.vstack([good, bad])
        scores = ga._fitness(combined)
        assert scores[0] > scores[1]

    def test_extreme_penalized(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[], seed=42)
        extreme = np.array([[0.70, 0.08, 0.14, 0.08]])
        normal = ga._target.copy().reshape(1, -1)
        combined = np.vstack([normal, extreme])
        scores = ga._fitness(combined)
        assert scores[0] > scores[1]


class TestRawObjective:
    def test_perfect_match_is_zero_distance(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[], seed=42)
        perfect = ga._target.copy().reshape(1, -1)
        obj = ga._raw_objective(perfect)
        assert obj[0] > -1e-9

    def test_cross_generation_comparable(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[], seed=42)
        pop1 = ga._initialize_population()
        pop2 = ga._initialize_population()
        # both populations should have consistent-scale objectives
        obj1 = ga._raw_objective(pop1)
        obj2 = ga._raw_objective(pop2)
        # values from two independent populations should be on the same scale
        assert obj1.max() < 0
        assert obj2.max() < 0


class TestEvolve:
    def test_converges_to_sum_one(self):
        ga = BudgetGA(budget_total=10000, num_days=5, preferences=["美食"], seed=42)
        best = ga.evolve()
        assert len(best) == NUM_GENES
        assert abs(best.sum() - 1.0) < 1e-9
        assert np.all(best >= GENE_MIN)

    def test_food_preference_boosts_dining(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=["美食"], seed=42)
        best = ga.evolve()
        dining_idx = CATEGORIES.index("dining")
        top2 = np.argsort(best)[-2:]
        assert dining_idx in top2, f"dining ({best[dining_idx]:.3f}) not in top 2: {best}"

    def test_comfort_preference_boosts_accommodation(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=["舒适"], seed=42)
        best = ga.evolve()
        acc_idx = CATEGORIES.index("accommodation")
        assert best[acc_idx] == best.max(), f"accommodation should be highest: {best}"

    def test_long_trip_favors_accommodation(self):
        ga_short = BudgetGA(budget_total=10000, num_days=1, preferences=[], seed=42)
        ga_long = BudgetGA(budget_total=10000, num_days=10, preferences=[], seed=42)
        best_short = ga_short.evolve()
        best_long = ga_long.evolve()
        acc_idx = CATEGORIES.index("accommodation")
        assert best_long[acc_idx] > best_short[acc_idx]

    def test_multi_destination_favors_transport(self):
        ga_single = BudgetGA(budget_total=10000, num_days=5, preferences=[],
                             num_destinations=1, seed=42)
        ga_multi = BudgetGA(budget_total=10000, num_days=5, preferences=[],
                            num_destinations=4, seed=42)
        best_single = ga_single.evolve()
        best_multi = ga_multi.evolve()
        transport_idx = CATEGORIES.index("transport")
        assert best_multi[transport_idx] > best_single[transport_idx]

    def test_reproducible_with_seed(self):
        ga1 = BudgetGA(budget_total=10000, num_days=3, preferences=["文化", "美食"], seed=123)
        ga2 = BudgetGA(budget_total=10000, num_days=3, preferences=["文化", "美食"], seed=123)
        assert np.allclose(ga1.evolve(), ga2.evolve())


class TestMutation:
    def test_does_not_mutate_input_in_place(self):
        ga = BudgetGA(budget_total=10000, num_days=3, preferences=[], seed=42)
        original = ga._initialize_population()[:10].copy()
        before = original.copy()
        _result = ga._polynomial_mutation(original)
        assert np.allclose(original, before), "mutation should not mutate input"


class TestOptimizeBudget:
    def test_returns_exact_total(self):
        result = optimize_budget(
            budget_total=10000, num_days=4,
            preferences=["美食", "文化"], seed=42,
        )
        assert set(result.keys()) == set(CATEGORIES)
        assert sum(result.values()) == 10000

    def test_all_categories_get_positive_amount(self):
        result = optimize_budget(
            budget_total=5000, num_days=2,
            preferences=["穷游"], seed=42,
        )
        for cat in CATEGORIES:
            assert result[cat] > 0, f"{cat} should get positive amount"

    def test_empty_preferences_works(self):
        result = optimize_budget(budget_total=20000, num_days=5, preferences=[], seed=42)
        assert all(v > 0 for v in result.values())
