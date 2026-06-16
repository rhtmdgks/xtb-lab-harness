# xTB Output Format (parsed fields)

The parser reads combined `stdout.log` + `stderr.log` and optional `charges` file.

## Total energy

Regex targets:

```text
TOTAL ENERGY               -5.0701048 Eh
FINAL SINGLE POINT ENERGY  -5.0701048 Eh
```

Stored as `total_energy_hartree` (Hartree).

## Dipole moment

Looks for the molecular dipole block:

```text
molecular dipole:
         total          1.85 (  0.00,  0.00,  1.85) debye
```

Stored as `dipole_moment_debye`.

## Partial charges

File: `charges` in the run directory (written by xTB).

```text
    #   Z          covCN         q      C6AA     α(0)
     1   8        1.000000    -0.6195    ...
```

Column index 3 (`q`) is parsed into `charge_summary`.

## Geometry optimization

- `xtbopt.xyz` present + `GEOMETRY OPTIMIZATION CONVERGED` → `geometry_optimized: true`
- `GEOMETRY OPTIMIZATION FAILED` → `geometry_optimized: false`

## Raw evidence

Every successful or failed run writes:

```text
data/runs/<candidate_id>/
  <candidate_id>.xyz
  stdout.log
  stderr.log
  xtbopt.xyz        (if optimization succeeded)
  charges           (if xTB wrote it)
```
