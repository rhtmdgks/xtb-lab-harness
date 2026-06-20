# xTB Output Format (parsed fields)

The parser reads combined `stdout.log` + `stderr.log`, the optional `charges` file, and falls back to stdout tables when needed.

## Total energy

Regex targets (uses the **last** match in combined output — post-optimization value):

```text
TOTAL ENERGY               -5.070544351073 Eh
FINAL SINGLE POINT ENERGY  -5.0701048 Eh
         :: total energy              -5.070222286727 Eh    ::
          | TOTAL ENERGY               -5.070544351073 Eh   |
```

Stored as `total_energy_hartree` (Hartree).

## Dipole moment

Supports legacy and modern xTB blocks:

```text
molecular dipole:
         total          1.85 (  0.00,  0.00,  1.85) debye
```

```text
molecular dipole:
                 x           y           z       tot (Debye)
   full:        0.000       0.000      -0.872       2.216
```

The modern format uses the `full:` row, last column (Debye).

Stored as `dipole_moment_debye`.

## Partial charges

Primary: `charges` file in the run directory.

Supported formats:

```text
   -0.56476049
    0.28238024
```

```text
    #   Z          covCN         q      C6AA     α(0)
     1   8 O        1.611    -0.565    24.359     6.661
```

Fallback: covCN/q table parsed from stdout when the file is empty or missing.

Column index 3 (`q`) in tabular form; single float per line in compact form.

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
