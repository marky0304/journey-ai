"""Genetic Algorithm budget optimizer for trip planning.

Replaces LLM-based budget splitting with a proper multi-objective GA that finds
the globally optimal allocation across transport / accommodation / attraction / dining
under total-budget and min-max-share constraints.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional

import numpy as np

# ── GA hyperparameters ──────────────────────────────────────────────
POP_SIZE: int = 200
GENERATIONS: int = 150
TOURNAMENT_SIZE: int = 3
ELITE_FRAC: float = 0.10
MUTATION_RATE: float = 0.10
MUT_STEP: float = 0.30
SBX_ETA: float = 20.0
MUT_ETA: float = 20.0

# Per-gene soft bounds — repaired via clipping + normalisation.
# Max is enforced through fitness penalties, not hard-clip.
GENE_MIN: float = 0.03
GENE_MAX_SOFT: float = 0.50

CATEGORIES: List[str] = ["transport", "accommodation", "attraction", "dining"]
NUM_GENES: int = len(CATEGORIES)

# Dirichlet concentration for initialisation (higher = more centred)
DIRICHLET_ALPHA: np.ndarray = np.array([3.0, 3.0, 3.0, 3.0], dtype=np.float64)


# ── Preference → category weight boost ──────────────────────────────
PREFERENCE_BOOST: Dict[str, Dict[str, float]] = {
    "transport": {
        "购物": 1.25, "商圈": 1.20, "逛街": 1.15, "商场": 1.10, "市场": 1.05,
    },
    "accommodation": {
        "舒适": 1.55, "度假": 1.45, "放松": 1.35, "休闲": 1.25, "享受": 1.40,
        "奢华": 1.55, "高端": 1.40, "酒店": 1.30, "民宿": 1.15,
    },
    "attraction": {
        "文化": 1.45, "博物馆": 1.40, "历史": 1.35, "古迹": 1.35, "艺术": 1.30,
        "展览": 1.20, "自然": 1.30, "户外": 1.30, "徒步": 1.25, "登山": 1.25,
        "海滩": 1.20, "风景": 1.25, "山水": 1.30, "刺激": 1.20, "冒险": 1.20,
        "极限": 1.15, "运动": 1.15, "摄影": 1.20, "拍照": 1.15, "打卡": 1.15,
    },
    "dining": {
        "美食": 1.70, "小吃": 1.45, "餐饮": 1.40, "料理": 1.35, "餐厅": 1.25,
        "饭店": 1.20, "夜市": 1.30, "火锅": 1.25, "烧烤": 1.20,
    },
}

ECONOMY_PREFS = {"穷游", "省钱", "经济", "实惠", "背包"}


class BudgetGA:
    """Genetic Algorithm for trip budget allocation."""

    def __init__(
        self,
        budget_total: float,
        num_days: int,
        preferences: List[str],
        travel_style: str = "balanced",
        num_destinations: int = 1,
        seed: Optional[int] = None,
    ) -> None:
        self.budget_total = budget_total
        self.num_days = max(num_days, 1)
        self.preferences = preferences
        self.travel_style = travel_style
        self.num_destinations = max(num_destinations, 1)

        self._rng = np.random.default_rng(seed)
        self._economy_mode = any(p in ECONOMY_PREFS for p in preferences)
        self._target = self._build_target_vector()

    # ── target allocation ───────────────────────────────────────────

    def _build_target_vector(self) -> np.ndarray:
        """Build ideal allocation vector [0..1] from preferences / style / days."""
        base = np.array([0.25, 0.30, 0.25, 0.20], dtype=np.float64)

        for pref in self.preferences:
            for i, cat in enumerate(CATEGORIES):
                boost = PREFERENCE_BOOST.get(cat, {}).get(pref)
                if boost is not None:
                    base[i] *= boost

        if self.num_days <= 2:
            base[0] *= 1.15
            base[3] *= 1.05
        elif self.num_days >= 7:
            base[1] *= 1.25
            base[0] *= 0.85

        if self.num_destinations >= 3:
            base[0] *= 1.30
            base[1] *= 0.85

        if self.travel_style == "relaxed":
            base[1] *= 1.25
            base[2] *= 0.85
            base[0] *= 0.90
        elif self.travel_style == "compact":
            base[2] *= 1.20
            base[0] *= 1.15
            base[1] *= 0.85

        if self._economy_mode:
            base = np.array([0.20, 0.40, 0.20, 0.20], dtype=np.float64)

        return base / base.sum()

    # ── population init ─────────────────────────────────────────────

    def _initialize_population(self) -> np.ndarray:
        raw = self._rng.dirichlet(DIRICHLET_ALPHA, size=POP_SIZE)
        return self._repair(raw)

    # ── repair ──────────────────────────────────────────────────────

    @staticmethod
    def _repair(chromosomes: np.ndarray) -> np.ndarray:
        for _ in range(6):
            chromosomes = np.clip(chromosomes, GENE_MIN, None)
            chromosomes /= chromosomes.sum(axis=1, keepdims=True)
        return chromosomes

    # ── fitness (shifted, for within-generation selection) ──────────

    def _fitness(self, population: np.ndarray) -> np.ndarray:
        raw = self._raw_objective(population)
        return raw - raw.min() + 0.01

    # ── raw objective (unshifted, for cross-generation tracking) ────

    def _raw_objective(self, population: np.ndarray) -> np.ndarray:
        dist = np.linalg.norm(population - self._target, axis=1)
        lower_penalty = np.maximum(0, 0.04 - population).sum(axis=1)
        upper_penalty = np.maximum(0, population - GENE_MAX_SOFT).sum(axis=1)
        balance_penalty = lower_penalty + upper_penalty
        return -(dist + 0.4 * balance_penalty)

    # ── selection ───────────────────────────────────────────────────

    def _tournament_select(self, population: np.ndarray, fitness: np.ndarray) -> np.ndarray:
        selected = np.empty_like(population)
        n = POP_SIZE
        for i in range(n):
            idxs = self._rng.integers(0, n, TOURNAMENT_SIZE)
            best = idxs[fitness[idxs].argmax()]
            selected[i] = population[best]
        return selected

    # ── SBX crossover ───────────────────────────────────────────────

    def _sbx_crossover(self, parents: np.ndarray) -> np.ndarray:
        n = len(parents)
        children = parents.copy()
        self._rng.shuffle(children)
        for i in range(0, n - 1, 2):
            if self._rng.random() > 0.90:
                continue
            p1, p2 = parents[i], parents[i + 1]
            c1, c2 = children[i].copy(), children[i + 1].copy()
            for j in range(NUM_GENES):
                u = self._rng.random()
                if u <= 0.50:
                    beta = (2 * u) ** (1 / (SBX_ETA + 1))
                else:
                    beta = (1 / (2 * (1 - u))) ** (1 / (SBX_ETA + 1))
                c1[j] = 0.5 * ((1 + beta) * p1[j] + (1 - beta) * p2[j])
                c2[j] = 0.5 * ((1 - beta) * p1[j] + (1 + beta) * p2[j])
            children[i], children[i + 1] = c1, c2
        return self._repair(children)

    # ── polynomial mutation ─────────────────────────────────────────

    def _polynomial_mutation(self, population: np.ndarray) -> np.ndarray:
        mutated = population.copy()
        n = len(mutated)
        for i in range(n):
            for j in range(NUM_GENES):
                if self._rng.random() < MUTATION_RATE:
                    u = self._rng.random()
                    delta = (
                        (2 * u) ** (1 / (MUT_ETA + 1)) - 1
                        if u <= 0.5
                        else 1 - (2 * (1 - u)) ** (1 / (MUT_ETA + 1))
                    )
                    mutated[i, j] += delta * MUT_STEP
        return self._repair(mutated)

    # ── main loop ───────────────────────────────────────────────────

    def evolve(self) -> np.ndarray:
        pop = self._initialize_population()
        elite_count = max(1, int(POP_SIZE * ELITE_FRAC))

        best_chromosome: Optional[np.ndarray] = None
        best_objective: float = -math.inf

        for _ in range(GENERATIONS):
            fitness = self._fitness(pop)
            raw_obj = self._raw_objective(pop)

            elite_idxs = np.argpartition(fitness, -elite_count)[-elite_count:]
            elites = pop[elite_idxs].copy()

            gen_best_idx = raw_obj.argmax()
            if raw_obj[gen_best_idx] > best_objective:
                best_objective = raw_obj[gen_best_idx]
                best_chromosome = pop[gen_best_idx].copy()

            selected = self._tournament_select(pop, fitness)
            children = self._sbx_crossover(selected)
            children = self._polynomial_mutation(children)
            children[:elite_count] = elites
            pop = children

        assert best_chromosome is not None
        return best_chromosome / best_chromosome.sum()


# ── public API ──────────────────────────────────────────────────────

def optimize_budget(
    budget_total: float,
    num_days: int,
    preferences: List[str],
    travel_style: str = "balanced",
    num_destinations: int = 1,
    seed: Optional[int] = None,
) -> Dict[str, int]:
    """Run GA and return category→amount mapping (integers)."""
    ga = BudgetGA(
        budget_total=budget_total,
        num_days=num_days,
        preferences=preferences,
        travel_style=travel_style,
        num_destinations=num_destinations,
        seed=seed,
    )
    shares = ga.evolve()

    amounts = [max(1, int(budget_total * s)) for s in shares]
    remainder = int(budget_total) - sum(amounts)
    # distribute leftover to categories with largest fractional parts
    if remainder > 0:
        fracs = [(i, budget_total * s - int(budget_total * s)) for i, s in enumerate(shares)]
        fracs.sort(key=lambda x: x[1], reverse=True)
        for i in range(min(remainder, len(fracs))):
            amounts[fracs[i][0]] += 1

    return dict(zip(CATEGORIES, amounts))
