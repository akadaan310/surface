// Exact rational arithmetic over BigInt. Used wherever a mathematical law must
// hold exactly; JavaScript `number` is never used to decide a law.

export class Q {
  readonly n: bigint;
  readonly d: bigint;

  private constructor(n: bigint, d: bigint) {
    this.n = n;
    this.d = d;
  }

  static of(n: bigint | number, d: bigint | number = 1n): Q {
    let nn = BigInt(n);
    let dd = BigInt(d);
    if (dd === 0n) throw new RangeError('Q.of: zero denominator is not a rational number');
    if (dd < 0n) {
      nn = -nn;
      dd = -dd;
    }
    const g = gcd(abs(nn), dd);
    return new Q(nn / g, dd / g);
  }

  static readonly zero = Q.of(0);
  static readonly one = Q.of(1);

  add(o: Q): Q {
    return Q.of(this.n * o.d + o.n * this.d, this.d * o.d);
  }
  sub(o: Q): Q {
    return Q.of(this.n * o.d - o.n * this.d, this.d * o.d);
  }
  mul(o: Q): Q {
    return Q.of(this.n * o.n, this.d * o.d);
  }
  neg(): Q {
    return Q.of(-this.n, this.d);
  }
  /** Field division. Throws on a zero divisor: there is no rational c with 0·c = a for a ≠ 0. */
  div(o: Q): Q {
    if (o.n === 0n) throw new RangeError('Q.div: zero has no multiplicative inverse in Q');
    return Q.of(this.n * o.d, this.d * o.n);
  }
  isZero(): boolean {
    return this.n === 0n;
  }
  eq(o: Q): boolean {
    return this.n === o.n && this.d === o.d;
  }
  toNumber(): number {
    return Number(this.n) / Number(this.d);
  }
  toString(): string {
    return this.d === 1n ? this.n.toString() : `${this.n}/${this.d}`;
  }
}

export function abs(a: bigint): bigint {
  return a < 0n ? -a : a;
}

export function gcd(a: bigint, b: bigint): bigint {
  a = abs(a);
  b = abs(b);
  while (b !== 0n) [a, b] = [b, a % b];
  return a === 0n ? 1n : a;
}

export function gcdInt(a: number, b: number): number {
  a = Math.abs(a);
  b = Math.abs(b);
  while (b) [a, b] = [b, a % b];
  return a;
}

/** Mathematical modulo: result in [0, m). */
export function mod(a: number, m: number): number {
  return ((a % m) + m) % m;
}
