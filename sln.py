from sympy import Matrix
import numpy as np
import multiprocessing as mp

# Define Montgomery power function for secp256k1
def montgomery_power(base, exp, mod):
    res = 1
    base = base % mod
    while exp > 0:
        if exp % 2 == 1:
            res = (res * base) % mod
        exp = exp >> 1
        base = (base * base) % mod
    return res

# Function to generate a prime factor base
def generate_factor_base(limit):
    primes = []
    num = 2
    while len(primes) < limit:
        if all(num % i != 0 for i in range(2, int(num**0.5) + 1)):
            primes.append(num)
        num += 1
    return primes

# Precompute the factor base
factor_base_size = 100
factor_base = generate_factor_base(factor_base_size)

# Function to find smooth numbers in a range (optimized further)
def find_smooth_numbers(start, end):
    smooth_numbers = []
    for num in range(start, end + 1):
        exps = []
        for p in factor_base:
            count = 0
            while num % p == 0:
                count += 1
                num //= p
            exps.append(count)
        if num == 1:
            smooth_numbers.append((num, exps))
    return smooth_numbers

# Function to solve linear equations using Lanczos algorithms
def solve_linear_equations(smooth_nums, G, n):
    A = Matrix([[f[1][i] for f in smooth_nums] for i in range(factor_base_size)]).T
    B = Matrix([G**f[0] % n for f in smooth_nums])

    X = A.LUsolve(B)

    logs = [(p, int(X[i])) for i, p in enumerate(factor_base)]
    return logs

# Function for multiprocessing
def process_range(args):
    start, end, G, n = args
    print(f"Processing range: {start}-{end}")
    smooth_nums = find_smooth_numbers(start, end)
    print(f"Found {len(smooth_nums)} smooth numbers in range {start}-{end}")
    return solve_linear_equations(smooth_nums, G, n)

# Use freeze_support for multiprocessing
if __name__ == '__main__':
    mp.freeze_support()

    # Parameters for secp256k1 curve and public key
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    a = 0
    b = 7
    n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
    Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

    pub_key_x = 0x26597xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    pub_key_y = 0x158b6xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    pub_point = (pub_key_x, pub_key_y)

    print("Calculating private key...")
    # Split the range into chunks for multiprocessing
    num_chunks = mp.cpu_count()
    chunk_size = (n // num_chunks) + 1
    ranges = [(i, min(i + chunk_size - 1, n), Gx, n) for i in range(1, n + 1, chunk_size)]

    # Perform multiprocessing
    with mp.Pool(processes=num_chunks) as pool:
        logs_list = pool.map(process_range, ranges)

    # Combine results from multiprocessing
    logs = []
    for logs_chunk in logs_list:
        logs.extend(logs_chunk)

    # Calculate private key using index calculus
    d = 1
    for p, a in logs:
        while montgomery_power(pub_point[0], d * a, p) != 1:
            d += 1
        if d >= n:
            break

    print(f"Private Key (d): {d}")
