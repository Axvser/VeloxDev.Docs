# 过渡动画 — 缓动曲线

每个内置族，都由库自己的 `Ease` 方法画出。表达式转写自 `Src/Core/VeloxDev.Core/TransitionSystem/Effects/Eases.cs` 中的代码，因此每条曲线都是引擎实际执行的计算 —— 不是重绘。

转写中只有一处改动：`Math.Pow(2, u)` 写成 `exp(u*ln2)`。绘图器的区间采样器对**非整数指数**的幂会返回空区间，导致整条曲线静默地画不出来 —— 无异常、无提示。`exp(u*ln2)` 与 `2^u` 在数学上相同；两者一致到 1e-16，也就是 double 舍入本身。灰线是 `Eases.Default`（线性），作为参照。

每张图把一个族的 `In`、`Out`、`InOut` 放在同一坐标轴上：`In` 起步慢并加速，`Out` 起步快并收敛，`InOut` 两者兼有。

## 所有族一览

十个族的 `Out` 方向放在同一张图上，比较它们的性格 —— 起步多突兀，以及哪些会过冲。

```plot
{
  "title": "Every family, Out",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.11, 1.48] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "sin(x*PI/2)", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^2", "color": "#61afef" },
    { "fn": "1 - (1-x)^3", "color": "#98c379" },
    { "fn": "1 - (1-x)^4", "color": "#e5c07b" },
    { "fn": "1 - (1-x)^5", "color": "#d19a66" },
    { "fn": "x == 1 ? 1 : 1 - exp((-10*x)*0.6931471805599453)", "color": "#e06c75" },
    { "fn": "sqrt(1 - (x-1)^2)", "color": "#c678dd" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : exp((-10*x)*0.6931471805599453)*sin((x*10 - 0.75)*2*PI/3) + 1", "color": "#f472b6" },
    { "fn": "x < 0.36363636 ? 7.5625*x^2 : x < 0.72727273 ? 7.5625*(x-0.54545455)^2 + 0.75 : x < 0.90909091 ? 7.5625*(x-0.81818182)^2 + 0.9375 : 7.5625*(x-0.95454545)^2 + 0.984375", "color": "#56b6c2" }
  ]
}
```

## Sine

```plot
{
  "title": "Eases.Sine — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "1 - cos(x*PI/2)", "color": "#4a9eff" },
    { "fn": "sin(x*PI/2)", "color": "#a78bfa" },
    { "fn": "-(cos(PI*x) - 1)/2", "color": "#f472b6" }
  ]
}
```

## Quad

```plot
{
  "title": "Eases.Quad — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x^2", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^2", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? 2*x^2 : 1 - (-2*x + 2)^2/2", "color": "#f472b6" }
  ]
}
```

## Cubic

```plot
{
  "title": "Eases.Cubic — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x^3", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^3", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? 4*x^3 : 1 - (-2*x + 2)^3/2", "color": "#f472b6" }
  ]
}
```

## Quart

```plot
{
  "title": "Eases.Quart — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x^4", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^4", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? 8*x^4 : 1 - (-2*x + 2)^4/2", "color": "#f472b6" }
  ]
}
```

## Quint

```plot
{
  "title": "Eases.Quint — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x^5", "color": "#4a9eff" },
    { "fn": "1 - (1-x)^5", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? 16*x^5 : 1 - (-2*x + 2)^5/2", "color": "#f472b6" }
  ]
}
```

## Expo

```plot
{
  "title": "Eases.Expo — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x == 0 ? 0 : exp((10*x - 10)*0.6931471805599453)", "color": "#4a9eff" },
    { "fn": "x == 1 ? 1 : 1 - exp((-10*x)*0.6931471805599453)", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : x < 0.5 ? exp((20*x - 10)*0.6931471805599453)/2 : (2 - exp((-20*x + 10)*0.6931471805599453))/2", "color": "#f472b6" }
  ]
}
```

## Circ

```plot
{
  "title": "Eases.Circ — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "1 - sqrt(1 - x^2)", "color": "#4a9eff" },
    { "fn": "sqrt(1 - (x-1)^2)", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? (1 - sqrt(1 - (2*x)^2))/2 : (sqrt(1 - (-2*x + 2)^2) + 1)/2", "color": "#f472b6" }
  ]
}
```

## Back

```plot
{
  "title": "Eases.Back — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.2, 1.2] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "2.70158*x^3 - 1.70158*x^2", "color": "#4a9eff" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? ((2*x)^2*((2.5949095 + 1)*2*x - 2.5949095))/2 : ((2*x-2)^2*((2.5949095 + 1)*(x*2-2) + 2.5949095) + 2)/2", "color": "#f472b6" }
  ]
}
```

## Elastic

```plot
{
  "title": "Eases.Elastic — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.51, 1.51] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : -exp((10*x - 10)*0.6931471805599453)*sin((x*10 - 10.75)*2*PI/3)", "color": "#4a9eff" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : exp((-10*x)*0.6931471805599453)*sin((x*10 - 0.75)*2*PI/3) + 1", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : x < 0.5 ? -(exp((20*x - 10)*0.6931471805599453)*sin((20*x - 11.125)*2*PI/4.5))/2 : (exp((-20*x + 10)*0.6931471805599453)*sin((20*x - 11.125)*2*PI/4.5))/2 + 1", "color": "#f472b6" }
  ]
}
```

## Bounce

```plot
{
  "title": "Eases.Bounce — In / Out / InOut",
  "grid": true,
  "xAxis": { "domain": [0, 1] },
  "yAxis": { "domain": [-0.1, 1.1] },
  "data": [
    { "fn": "x", "color": "#888888", "skipTip": true },
    { "fn": "1 - ((1-x) < 0.36363636 ? 7.5625*(1-x)^2 : (1-x) < 0.72727273 ? 7.5625*((1-x)-0.54545455)^2 + 0.75 : (1-x) < 0.90909091 ? 7.5625*((1-x)-0.81818182)^2 + 0.9375 : 7.5625*((1-x)-0.95454545)^2 + 0.984375)", "color": "#4a9eff" },
    { "fn": "x < 0.36363636 ? 7.5625*x^2 : x < 0.72727273 ? 7.5625*(x-0.54545455)^2 + 0.75 : x < 0.90909091 ? 7.5625*(x-0.81818182)^2 + 0.9375 : 7.5625*(x-0.95454545)^2 + 0.984375", "color": "#a78bfa" },
    { "fn": "x < 0.5 ? (1 - ((1-2*x) < 0.36363636 ? 7.5625*(1-2*x)^2 : (1-2*x) < 0.72727273 ? 7.5625*((1-2*x)-0.54545455)^2 + 0.75 : (1-2*x) < 0.90909091 ? 7.5625*((1-2*x)-0.81818182)^2 + 0.9375 : 7.5625*((1-2*x)-0.95454545)^2 + 0.984375))/2 : (1 + ((2*x-1) < 0.36363636 ? 7.5625*(2*x-1)^2 : (2*x-1) < 0.72727273 ? 7.5625*((2*x-1)-0.54545455)^2 + 0.75 : (2*x-1) < 0.90909091 ? 7.5625*((2*x-1)-0.81818182)^2 + 0.9375 : 7.5625*((2*x-1)-0.95454545)^2 + 0.984375))/2", "color": "#f472b6" }
  ]
}
```

**预期结果：** 每张图显示同族的 `In`（慢起）、`Out`（快起后收敛）与 `InOut`（慢起、快中段、收敛）三条曲线；`Back` 与 `Elastic` 会明显越过 `y = 1` 再回来。
