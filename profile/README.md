<a href="https://starworks.dev">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/hero-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/hero-light.svg">
    <img alt="Starworks: an independent studio making games, and the engine they run on." src="assets/hero-light.svg" width="100%">
  </picture>
</a>

<div align="center">

[Website](https://starworks.dev) · [Arcane](https://starworks.dev/arcane) · [Astra](https://starworks.dev/astra) · [Manifold2D](https://starworks.dev/manifold)

</div>

We make games, and we build the technology under them in the open. Every layer of our stack is a library you can take on its own: an ECS, a 2D physics engine, a shared foundation, and the engine that ties them together.

| Project | What it is | Language | License | Build |
|---|---|---|---|---|
| [**Arcane**](https://github.com/StarworksDev/Arcane) | Game engine + editor | C++23 | BSL 1.1 → MIT | [![CI](https://github.com/StarworksDev/Arcane/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/StarworksDev/Arcane/actions/workflows/ci.yml?query=branch%3Amain) |
| [**Astra**](https://github.com/StarworksDev/Astra) | Entity Component System | C++20 | MIT | [![CI](https://github.com/StarworksDev/Astra/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/StarworksDev/Astra/actions/workflows/ci.yml?query=branch%3Amain) |
| [**Manifold2D**](https://github.com/StarworksDev/Manifold2D) | Deterministic 2D physics | C++23 | MIT | [![CI](https://github.com/StarworksDev/Manifold2D/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/StarworksDev/Manifold2D/actions/workflows/ci.yml?query=branch%3Amain) |
| [**Mosaic**](https://github.com/StarworksDev/Mosaic) | Zero-dependency foundation | C++23 | MIT | [![CI](https://github.com/StarworksDev/Mosaic/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/StarworksDev/Mosaic/actions/workflows/ci.yml?query=branch%3Amain) |
| [**hero3d**](https://github.com/StarworksDev/hero3d) | Text + UI on planes in perspective | TypeScript | MIT | `npm i @starworks-dev/hero3d` |

## The stack

<a href="https://starworks.dev/mosaic">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/stack-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/stack-light.svg">
  <img alt="Each route runs from a product to what it is built on. Arcane builds on Astra, Manifold2D and Mosaic; Astra and Manifold2D build on Mosaic; Mosaic needs only the C++ standard library." src="assets/stack-light.svg" width="100%">
</picture>
</a>

## Projects

### [Arcane](https://github.com/StarworksDev/Arcane) &nbsp;·&nbsp; game engine
**The C++23 engine our games run on.**
It renders through Direct3D 12 and Vulkan, runs its world on Astra and its physics on Manifold2D, and hosts your game as a module it can reload while you play: rebuild, and the live simulation carries over. The editor, the standalone runtime and the dedicated server all run the same game. Windows is home; Linux and macOS build and pass the test suite in CI.

### [Astra](https://github.com/StarworksDev/Astra) &nbsp;·&nbsp; ECS
**High-performance archetype ECS for modern C++.**
Entities with the same components share 16 KB chunks sized for the cache, and the hot loops pick up SSE, AVX2 or NEON on their own. Queries are checked at compile time, and hierarchies live outside component storage so they don't fragment it. Header-only: drop it into any C++20 project.

### [Manifold2D](https://github.com/StarworksDev/Manifold2D) &nbsp;·&nbsp; 2D physics
**Deterministic 2D rigid-body physics, modeled on Box2D v3.**
A sub-stepped soft-constraint solver, seven joint types, continuous collision for fast movers, and your choice of broadphase. The same inputs replay to the same results, even across broadphase backends. Nothing but the standard library.

### [Mosaic](https://github.com/StarworksDev/Mosaic) &nbsp;·&nbsp; foundation
**One foundation under every Starworks product.**
The zero-dependency layer beneath Arcane, Astra and Manifold2D: platform detection, deterministic SIMD, and the seams every component plugs into. It starts no threads of its own; the host hands it a scheduler, a log sink and an assert handler.

### [hero3d](https://github.com/StarworksDev/hero3d) &nbsp;·&nbsp; web
**Real interfaces, flying in 3D: sharp, clickable, accessible, and tiny.**
Text and UI on planes in perspective, drawn with Canvas 2D, with real HTML pinned on top wherever something has to be clicked or read by a screen reader. It draws the hero scenes on [starworks.dev](https://starworks.dev); a typical one is about 3 KB gzipped. `npm i @starworks-dev/hero3d`

## Licensing

| | License |
|---|---|
| Astra, Manifold2D, Mosaic, hero3d | MIT |
| Arcane | [Business Source License 1.1](https://github.com/StarworksDev/Arcane/blob/main/LICENSE): free to use and to ship games with, provided your game's credits say *"Made with the Arcane Engine"*. It may not be used to offer a competing engine product. Each version becomes MIT four years after its release. |

<div align="center">
<sub>Made by Starworks · <a href="https://starworks.dev">starworks.dev</a></sub>
</div>
