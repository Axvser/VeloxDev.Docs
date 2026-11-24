# Verification and Complete Code

The WinUI editor is verified the same way as the desktop XAML adapters, with one extra check: the offset frame has to survive deep zoom.

## Pages

- [Run and Verify](00_run-and-verify/index.md) — the run command and what each interaction should do.
- [Complete Code](01_complete-code/index.md) — project, manifest, bootstrap, ViewModels, selector and surface.
- [Link View](02_link-view/index.md) — the offset-frame link control, plus the run declaration.

Build the surface first, then the link view; the link view is the one class whose geometry depends on the canvas translation the surface publishes.
