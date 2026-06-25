import time
from os import urandom
from tinyec.ec import SubGroup, Curve
from tqdm import tqdm, trange

# Note: Ensure 'binarySearch' and 'wordAdder' modules are accessible in your environment
from binarySearch import binarySearch
from wordAdder import multiplyNum

def main():
    # --- SECP256K1 Curve Configuration ---
    curve_name = 'secp256k1'
    p = 0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f
    n = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141
    a = 0x0000000000000000000000000000000000000000000000000000000000000000
    b = 0x0000000000000000000000000000000000000000000000000000000000000007
    h = 1

    # --- Public Key Input & Validation ---
    try:
        x_input = input("Please Enter Your Public Key X Coordinate In Hexadecimal Format: ")
        y_input = input("Please Enter Your Public Key Y Coordinate In Hexadecimal Format: ")
        X = int(x_input, 16)
        Y = int(y_input, 16)
    except ValueError:
        print("Error: Invalid hexadecimal input.")
        return

    # Verify if the point lies on the secp256k1 curve: y^2 = x^3 + 7 (mod p)
    if (pow(X, 3, p) + 7) % p != pow(Y, 2, p) % p:
        print(
            "The Public Key X and Y Coordinates You Entered Are NOT Valid.\n"
            "NOTE: Do not include 02, 03, or 04 at the beginning of the X coordinate.\n"
            "Please try again with valid coordinates."
        )
        return

    g = (X, Y)
    curve1 = Curve(a, b, SubGroup(p, g, n, h), curve_name)
    entered_public_key = curve1.g * 1

    # --- Setup Parameters ---
    # N represents the group order curve configuration parameter
    N = 115792089237316195423570985008687907852837564279074904382605163141518161494337
    half = 57896044618658097711785492504343953926418782139537452191302581570759080747169

    try:
        list_size = int(input("Please Enter the Size of the Collision List (Recommended ~10,000): "))
    except ValueError:
        print("Invalid size entered. Defaulting to 10000.")
        list_size = 10000

    total_steps = list_size * 2
    bb_step = list_size

    # --- Step 1: Generate & Populate Collision List ---
    print("Creating Collision List... Please Wait...")
    collision_list = []
    
    # Initialize point position
    place = entered_public_key * pow(half, list_size, N)
    collision_list.append((place.x, -list_size))
    
    current_modifier = -list_size + 1
    
    for _ in trange(total_steps, ascii=True, ncols=100, colour='#00ff00', unit='Keys Stored', desc='Keys Stored In Memory...'):
        iterated_multiple = place + place
        collision_list.append((iterated_multiple.x, current_modifier))
        place = iterated_multiple
        current_modifier += 1

    # --- Step 2: Sort Collision List for Binary Search ---
    print("Sorting List... Please Wait...")
    collision_list.sort(key=lambda i: i[0])
    tuple_collision_list = tuple(collision_list)
    print("List Sorted... Searching For Key")

    # --- Step 3: Search Loop ---
    key_found = False
    while not key_found:
        start_time = time.process_time()
        
        # Generate pseudorandom 32-byte integer space safely
        random_bytes = urandom(32)[2:]
        priv_key = int(random_bytes.hex(), 16) % N
        private_key_base = (priv_key * pow(half, bb_step, N)) % N
        
        new_key = multiplyNum(private_key_base)
        
        for hash_iteration in trange(total_steps, ascii=True, ncols=100, colour='#00ff00', unit='Comparisons', desc='Searching...'):
            key_to_find = int(new_key.x)
            result = binarySearch(tuple_collision_list, key_to_find)
            
            if result != -1:
                # Collision found; recover the exponent mapping
                offset = result[1]
                if offset <= 0:
                    recovered_factor = (private_key_base * pow(2, hash_iteration, N) * pow(2, abs(offset), N)) % N
                else:
                    recovered_factor = (private_key_base * pow(half, hash_iteration, N) * pow(2, abs(offset), N)) % N
                
                recovered_key = multiplyNum(recovered_factor)
                if recovered_key.y != entered_public_key.y:
                    recovered_factor = N - recovered_factor
                
                print("\nX-Coordinate of Collision Key Found:", result)
                print("Collision PrivateKey Base:", private_key_base)
                print("Recovered Private Key:", recovered_factor)
                key_found = True
                return
            else:
                new_key += new_key

        elapsed_time = time.process_time() - start_time
        if elapsed_time > 0:
            print(f"Average Random Key Strings Created Per Second: {int(total_steps // elapsed_time)}")
            print(f"Average Seconds per Round: {elapsed_time:.4f}")

if __name__ == "__main__":
    main()
