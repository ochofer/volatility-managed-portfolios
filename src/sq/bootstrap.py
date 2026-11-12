"""
Ledoit and Wolf (2008): inference on the difference of two Sharpe ratios
measured on the same months.

    Ledoit, O. and Wolf, M. (2008). Robust performance hypothesis testing with
    the Sharpe ratio. Journal of Empirical Finance 15, 850-859.

The difference Delta = mu_1 / sigma_1 - mu_2 / sigma_2 is a smooth function of
four means, those of r_1, r_2, r_1^2 and r_2^2 (sigma^2 = E[r^2] - mu^2). Its
standard error comes from the delta method: the gradient of the function times
the long-run covariance matrix Psi of the four series, which allows the months
to be correlated with one another and the returns to have fat tails.

  On the sample itself, Psi is the prewhitened Parzen-kernel estimate with
  Andrews' (1991) automatic bandwidth. Ledoit and Wolf propose the prewhitened
  QS kernel of Andrews and Monahan (1992) and report that the prewhitened
  Parzen kernel "yields very similar performance" (section 3.2.2 and its
  footnote 8, p. 854), and that results with it were "virtually identical"; its
  finite support makes it "somewhat more convenient to implement" (Remark 4.1,
  p. 857).

  The circular block bootstrap resamples blocks of consecutive months, wrapping
  from the last month to the first, so that the dependence within a block is
  kept. On each bootstrap sample, Psi is the average outer product of the
  blocks' scaled means, the estimate that matches the resampling.

  The studentised statistic |Delta* - Delta_hat| / se* is computed on every
  bootstrap sample. Its 95th percentile z* gives the symmetric interval
  Delta_hat +/- z* se(Delta_hat), and the share of bootstrap statistics at least
  as large as |Delta_hat| / se(Delta_hat) gives the p-value of a zero
  difference.

The paper chooses the block size by its Algorithm 3.1, a calibration on data
simulated from a model fitted to the sample (p. 854); this study fixes it at 12
months in its constants, and every caller passes it.

The module depends on numpy alone, so that another study can import it
unchanged. Sharpe ratios here are monthly and use the population variance,
E[r^2] - mu^2, as Ledoit and Wolf do; multiply by the square root of 12 to
annualise.
"""
from __future__ import annotations

import numpy as np

__all__ = ["sharpe_difference", "standard_error", "circular_block_indices", "test", "simulate_null_pair", "size_check"]


def _moments(r1: np.ndarray, r2: np.ndarray):
    return r1.mean(), r2.mean(), (r1 ** 2).mean(), (r2 ** 2).mean()


def _delta(mu1, mu2, g1, g2):
    return mu1 / np.sqrt(g1 - mu1 ** 2) - mu2 / np.sqrt(g2 - mu2 ** 2)


def _gradient(mu1, mu2, g1, g2) -> np.ndarray:
    """The gradient of Delta with respect to (mu1, mu2, g1, g2); works on arrays of draws too."""
    s1, s2 = (g1 - mu1 ** 2) ** 1.5, (g2 - mu2 ** 2) ** 1.5
    return np.stack([g1 / s1, -g2 / s2, -0.5 * mu1 / s1, 0.5 * mu2 / s2], axis=-1)


def sharpe_difference(r1, r2) -> float:
    """The monthly Sharpe ratio of r1 minus that of r2, population variances."""
    r1, r2 = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    return float(_delta(*_moments(r1, r2)))


def _parzen(x: float) -> float:
    x = abs(x)
    if x <= 0.5:
        return 1 - 6 * x ** 2 + 6 * x ** 3
    if x <= 1:
        return 2 * (1 - x) ** 3
    return 0.0


def _gamma(v: np.ndarray, j: int) -> np.ndarray:
    """The sample autocovariance matrix at lag j, divided by T."""
    t = len(v)
    return v[j:].T @ v[:t - j] / t


def _ar1(x: np.ndarray):
    """Least-squares AR(1) with an intercept: the coefficient and the residual variance."""
    y, z = x[1:], x[:-1]
    zc, yc = z - z.mean(), y - y.mean()
    rho = float(zc @ yc / (zc @ zc))
    resid = yc - rho * zc
    return rho, float(resid @ resid / len(resid))


def _andrews_alpha(v: np.ndarray) -> float:
    """Andrews' (1991) plug-in quantity for the Parzen kernel, from univariate AR(1) fits, equal weights."""
    num = den = 0.0
    for i in range(v.shape[1]):
        rho, sig2 = _ar1(v[:, i])
        num += 4 * rho ** 2 * sig2 ** 2 / (1 - rho) ** 8
        den += sig2 ** 2 / (1 - rho) ** 4
    return num / den


def _psi_parzen(v: np.ndarray) -> np.ndarray:
    """The Parzen-kernel long-run covariance with Andrews' bandwidth 2.6614 (alpha T)^(1/5)."""
    t, p = v.shape
    bandwidth = 2.6614 * (_andrews_alpha(v) * t) ** 0.2
    psi = _gamma(v, 0)
    j = 1
    while j < bandwidth and j < t:
        g = _gamma(v, j)
        psi = psi + _parzen(j / bandwidth) * (g + g.T)
        j += 1
    return psi * t / (t - p)


def standard_error(r1, r2) -> float:
    """The standard error of the monthly Sharpe ratio difference: the delta method with the prewhitened
    Parzen-kernel estimate of Psi (a VAR(1) fitted to the four series, its singular values held within
    +/- 0.97, the kernel estimate on the residuals, then recoloured)."""
    r1, r2 = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    mu1, mu2, g1, g2 = _moments(r1, r2)
    grad = _gradient(mu1, mu2, g1, g2)
    v = np.column_stack([r1 - mu1, r2 - mu2, r1 ** 2 - g1, r2 ** 2 - g2])
    t = len(v)
    x, y = v[:-1], v[1:]
    a = np.linalg.lstsq(x, y, rcond=None)[0].T                  # y_t = A y_{t-1} + e_t, no intercept
    u, d, vt = np.linalg.svd(a)
    a = u @ np.diag(np.clip(d, -0.97, 0.97)) @ vt
    resid = y - x @ a.T
    inv = np.linalg.inv(np.eye(4) - a)
    psi = inv @ _psi_parzen(resid) @ inv.T
    return float(np.sqrt(grad @ psi @ grad / t))


def circular_block_indices(months: int, block: int, draws: int, rng: np.random.Generator) -> np.ndarray:
    """Indices of `draws` circular block bootstrap samples: floor(months / block) blocks of `block`
    consecutive months each, every block starting at a month drawn uniformly, wrapping past the last
    month to the first. Shape (draws, blocks * block)."""
    n_blocks = months // block
    starts = rng.integers(0, months, size=(draws, n_blocks))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % months
    return idx.reshape(draws, n_blocks * block)


def _bootstrap_statistics(r1, r2, delta_hat, block, draws, rng):
    t = len(r1)
    idx = circular_block_indices(t, block, draws, rng)
    a, b = r1[idx], r2[idx]
    n = idx.shape[1]
    n_blocks = n // block
    mu1, mu2 = a.mean(axis=1), b.mean(axis=1)
    g1, g2 = (a ** 2).mean(axis=1), (b ** 2).mean(axis=1)
    delta = _delta(mu1, mu2, g1, g2)
    y = np.stack([a - mu1[:, None], b - mu2[:, None], a ** 2 - g1[:, None], b ** 2 - g2[:, None]], axis=-1)
    zeta = np.sqrt(block) * y.reshape(draws, n_blocks, block, 4).mean(axis=2)
    psi = np.einsum("dki,dkj->dij", zeta, zeta) / n_blocks
    grad = _gradient(mu1, mu2, g1, g2)
    se = np.sqrt(np.einsum("di,dij,dj->d", grad, psi, grad) / n)
    return np.abs(delta - delta_hat) / se


def test(r1, r2, block: int = 12, draws: int = 2000, level: float = 0.95, seed: int | np.random.Generator = 0) -> dict:
    """Ledoit and Wolf's test of a zero Sharpe ratio difference, r1 minus r2, on paired monthly returns.

    Returns the monthly difference, its standard error, the symmetric studentised interval at `level`, its
    half-width, the critical value z*, the p-value of a zero difference and whether the interval excludes
    zero. The same seed gives the same result."""
    r1, r2 = np.asarray(r1, dtype=float), np.asarray(r2, dtype=float)
    if r1.shape != r2.shape or r1.ndim != 1:
        raise ValueError("two one-dimensional series over the same months are needed")
    rng = seed if isinstance(seed, np.random.Generator) else np.random.default_rng(seed)
    delta_hat = sharpe_difference(r1, r2)
    se = standard_error(r1, r2)
    stats = _bootstrap_statistics(r1, r2, delta_hat, block, draws, rng)
    z_star = float(np.quantile(stats, level))
    d = abs(delta_hat) / se
    p = (int((stats >= d).sum()) + 1) / (draws + 1)
    half = z_star * se
    return {"difference": delta_hat, "se": se, "lower": delta_hat - half, "upper": delta_hat + half,
            "half_width": half, "critical": z_star, "p_value": p, "excludes_zero": bool(abs(delta_hat) > half),
            "months": len(r1), "block": block, "draws": draws, "level": level}


def simulate_null_pair(months: int, mean: float, sd: float, rho: float, dof: int,
                       rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Two monthly return series with the same mean and standard deviation, so the same Sharpe ratio, and
    correlation rho: a common Student-t shock and one own shock each, every shock scaled to variance 1."""
    scale = np.sqrt(dof / (dof - 2))
    common, own1, own2 = (rng.standard_t(dof, size=(3, months)) / scale)
    e1 = np.sqrt(rho) * common + np.sqrt(1 - rho) * own1
    e2 = np.sqrt(rho) * common + np.sqrt(1 - rho) * own2
    return mean + sd * e1, mean + sd * e2


def size_check(pairs: int, months: int, mean: float, sd: float, rho: float, dof: int, seed: int,
               block: int = 12, draws: int = 2000, level: float = 0.95) -> dict:
    """The share of simulated pairs with equal Sharpe ratios whose interval excludes zero: the test's
    rejection rate under the null, which should be close to 1 - level. Returns the rate, the count and
    each pair's difference and p-value."""
    root = np.random.SeedSequence(seed)
    data_seed, boot_seed = root.spawn(2)
    data_rng = np.random.default_rng(data_seed)
    boot_rngs = [np.random.default_rng(s) for s in boot_seed.spawn(pairs)]
    rejected, p_values, differences = [], [], []
    for k in range(pairs):
        r1, r2 = simulate_null_pair(months, mean, sd, rho, dof, data_rng)
        out = test(r1, r2, block=block, draws=draws, level=level, seed=boot_rngs[k])
        rejected.append(out["excludes_zero"])
        p_values.append(out["p_value"])
        differences.append(out["difference"])
    rejected = np.array(rejected)
    return {"rate": float(rejected.mean()), "rejected": int(rejected.sum()), "pairs": pairs,
            "p_values": np.array(p_values), "differences": np.array(differences)}
