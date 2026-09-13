# Transition — 缓动曲线图

内置的全部缓动族，均由库自身的 `Ease` 方法绘出。表达式就是
`Src/Core/VeloxDev.Core/TransitionSystem/Eases.cs` 里的代码本身，因此每条曲线画的都是
引擎真正执行的那次计算，而不是它的近似重绘。灰色参考线是 `Eases.Default`（线性）。

每张图把同一族的 `In`、`Out`、`InOut` 画在同一坐标系里：`In` 起步慢、随后加速，
`Out` 起步快、随后落定，`InOut` 两者兼有。

## 全部曲线一览

十个缓动族的 `Out` 方向画在同一坐标系里，用来比较它们的性格——起步有多陡、哪些会冲过头。

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
    { "fn": "x == 1 ? 1 : 1 - 2^(-10*x)", "color": "#e06c75" },
    { "fn": "sqrt(1 - (x-1)^2)", "color": "#c678dd" },
    { "fn": "1 + 2.70158*(x-1)^3 + 1.70158*(x-1)^2", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : 2^(-10*x)*sin((x*10 - 0.75)*2*PI/3) + 1", "color": "#f472b6" },
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
    { "fn": "x == 0 ? 0 : 2^(10*x - 10)", "color": "#4a9eff" },
    { "fn": "x == 1 ? 1 : 1 - 2^(-10*x)", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : x < 0.5 ? 2^(20*x - 10)/2 : (2 - 2^(-20*x + 10))/2", "color": "#f472b6" }
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
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : -2^(10*x - 10)*sin((x*10 - 10.75)*2*PI/3)", "color": "#4a9eff" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : 2^(-10*x)*sin((x*10 - 0.75)*2*PI/3) + 1", "color": "#a78bfa" },
    { "fn": "x == 0 ? 0 : x == 1 ? 1 : x < 0.5 ? -(2^(20*x - 10)*sin((20*x - 11.125)*2*PI/4.5))/2 : (2^(-20*x + 10)*sin((20*x - 11.125)*2*PI/4.5))/2 + 1", "color": "#f472b6" }
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
