import multiprocessing as mp
import time
from sympy import Matrix

def generate_factor_base(limit):
    """Generates the first 'limit' prime numbers using an incremental sieve."""
    primes = []
    candidate = 2
    while len(primes) < limit:
        if all(candidate % i != 0 for i in range(2, int(candidate**0.5) + 1)):
            primes.append(candidate)
        candidate += 1
    return primes

# Precompute global factor base parameters
FACTOR_BASE_SIZE = 100
FACTOR_BASE = generate_factor_base(FACTOR_BASE_SIZE)

def find_smooth_numbers(start, end):
    """Finds smooth numbers relative to the FACTOR_BASE within a specific range."""
    smooth_numbers = []
    for original_num in range(start, end + 1):
        temp = original_num
        exps = []
        for p in FACTOR_BASE:
            count = 0
            while temp % p == 0:
                count += 1
                temp //= p
            exps.append(count)
        if temp == 1:
            smooth_numbers.append((original_num, exps))
    return smooth_numbers

def solve_linear_equations(smooth_nums, G, n):
    """Constructs and solves the linear system using SymPy's LU decomposition."""
    if not smooth_nums:
        return []
        
    # Transpose the exponents matrix
    A = Matrix([[f[1][i] for f in smooth_nums] for i in range(FACTOR_BASE_SIZE)]).T
    B = Matrix([pow(G, f[0], n) for f in smooth_nums])

    X = A.LUsolve(B)
    logs = [(p, int(X[i])) for i, p in enumerate(FACTOR_BASE)]
    return logs

def process_range(args):
    """Worker function for processing a partitioned range."""
    start, end, G, n = args
    print(f"Processing range: {start} - {end}")
    smooth_nums = find_smooth_numbers(start, end)
    print(f"Found {len(smooth_nums)} smooth numbers in range {start} - {end}")
    return solve_linear_equations(smooth_nums, G, n)

if __name__ == '__main__':
    mp.freeze_support()

    # --- secp256k1 Parameters ---
    p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
    n = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
    Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798

    # --- Target Public Key Coordinates ---
    pub_key_x = 0x4b83426cf9bff257261d87f2f2858b51b2eea756c0123c7e05bc0a007425c9f2
    pub_key_y = 0x47f89e94bc377d9078223f363da4522497a4322406a16deaa8eaace5f2f4b508
    pub_point = (pub_key_x, pub_key_y)

    print("Initiating calculations...")
    
    # Partitioning calculation space across available CPU threads
    num_chunks = mp.cpu_count()
    chunk_size = (n // num_chunks) + 1
    ranges = [(i, min(i + chunk_size - 1, n), Gx, n) for i in range(1, n + 1, chunk_size)]

    # Executing multiprocessing pool
    with mp.Pool(processes=num_chunks) as pool:
        logs_list = pool.map(process_range, ranges)

    # Consolidate factors
    logs = []
    for logs_chunk in logs_list:
        logs.extend(logs_chunk)

    # --- Reconstruct Private Key Exponent ---
    d = 1
    for prime, alpha in logs:
        # Utilizing native fast modular exponentiation
        while pow(pub_point[0], d * alpha, prime) != 1:
            d += 1
        if d >= n:
            break

    print(f"Calculated Private Key: {d}")
