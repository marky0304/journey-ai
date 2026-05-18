export function HowItWorks() {
  const steps = [
    { step: '01', title: '输入需求', desc: '告诉我们目的地、日期、预算和偏好' },
    { step: '02', title: 'AI 规划', desc: '多个 Agent 同时工作，秒级生成方案' },
    { step: '03', title: '轻松出行', desc: '确认行程，一键预订，旅途无忧' },
  ]
  return (
    <section className="py-20">
      <div className="container mx-auto px-4">
        <h2 className="text-center text-3xl font-bold">三步开启旅程</h2>
        <div className="mt-12 grid gap-8 md:grid-cols-3">
          {steps.map((s) => (
            <div key={s.step} className="text-center">
              <span className="text-4xl font-bold text-primary/30">{s.step}</span>
              <h3 className="mt-2 text-xl font-semibold">{s.title}</h3>
              <p className="mt-1 text-muted-foreground">{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
