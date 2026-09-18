#!/usr/bin/env python3
"""
Bee Virus Primer Analysis Script
Analyzes primer pairs for DWV-A, DWV-B, and ABPV viruses
"""

import re

# Define primers
primers = {
    # DWV-A primers
    "DWV-A_5663F": "GCTCTTACGTGCGAGTCGTA",
    "DWV-A_6662R": "TGTGAATTCAGTGTCGCCC", 
    "DWV-A_6378F": "GGTGCGGAAATTAGTGC",
    "DWV-A_7259R": "CGCTTGCAACCACACTT",
    "DWV-A_8106F": "GGCGATGGTGTTTGTGGTTC",
    "DWV-A_9010R": "GCAGCTCGATAGGATGCCAT",
    
    # DWV-B primers  
    "DWV-B_5612F": "ACGGGCATTAAGTGTGTCGT",
    "DWV-B_6604R": "AACCAAACGCTCCAAAGCTG",
    "DWV-B_7464F": "GACCTCAGGGATCAACGCAA", 
    "DWV-B_8406R": "AACGGATCATGTGGCGCTAT",
    "DWV-B_8376F": "GAGACCCAAGAATAGCGCCA",
    "DWV-B_9305R": "TACCTTGCCAAGCCAATCGA",
    
    # ABPV primers
    "ABPV_483F": "GCAGTTTGAATTGGAGGGG",
    "ABPV_1346R": "TGGCTGCTCTTCCCAAATCC",
    "ABPV_4327F": "ACCAGTGGGCAGATTGAGTG", 
    "ABPV_5171R": "TTAGTGCGTTTTCCGGTCCA"
}

def extract_position_from_name(primer_name):
    """Extract genomic position from primer name"""
    match = re.search(r'_(\d+)[FR]', primer_name)
    return int(match.group(1)) if match else None

def calculate_tm_basic(sequence):
    """Basic Tm calculation using Wallace rule"""
    return 4 * (sequence.count('G') + sequence.count('C')) + 2 * (sequence.count('A') + sequence.count('T'))

def calculate_gc_content(sequence):
    """Calculate GC content percentage"""
    gc_count = sequence.count('G') + sequence.count('C')
    return (gc_count / len(sequence)) * 100

def analyze_primers():
    """Analyze all primers and identify potential pairs"""
    print("=" * 80)
    print("BEE VIRUS PRIMER ANALYSIS")
    print("=" * 80)
    
    # Group primers by virus
    virus_groups = {}
    for name, seq in primers.items():
        virus = name.split('_')[0]
        if virus not in virus_groups:
            virus_groups[virus] = {}
        virus_groups[virus][name] = seq
    
    print("\n1. PRIMER CHARACTERISTICS")
    print("-" * 50)
    
    for virus, primer_dict in virus_groups.items():
        print(f"\n{virus} PRIMERS:")
        for name, seq in primer_dict.items():
            direction = "Forward" if name.endswith('F') else "Reverse"
            position = extract_position_from_name(name)
            tm = calculate_tm_basic(seq)
            gc = calculate_gc_content(seq)
            
            print(f"  {name:15} | {seq:20} | {len(seq):2}bp | {direction:7} | Pos: {position:4} | Tm: {tm:2}°C | GC: {gc:.1f}%")
    
    print("\n2. POTENTIAL AMPLICON CALCULATIONS")
    print("-" * 50)
    
    # Calculate amplicons for each virus
    for virus, primer_dict in virus_groups.items():
        print(f"\n{virus} AMPLICONS:")
        
        # Separate forward and reverse primers
        forward_primers = {k: v for k, v in primer_dict.items() if k.endswith('F')}
        reverse_primers = {k: v for k, v in primer_dict.items() if k.endswith('R')}
        
        # Calculate all possible combinations
        for f_name, f_seq in forward_primers.items():
            f_pos = extract_position_from_name(f_name)
            for r_name, r_seq in reverse_primers.items():
                r_pos = extract_position_from_name(r_name)
                
                if f_pos and r_pos and r_pos > f_pos:
                    amplicon_length = r_pos - f_pos + len(r_seq)
                    print(f"  {f_name} + {r_name}: ~{amplicon_length:4} bp")
    
    print("\n3. MOST LIKELY PRIMER PAIRS")
    print("-" * 50)
    
    # Common amplicon size ranges for different applications
    expected_pairs = [
        ("DWV-A_5663F", "DWV-A_6662R", "~999 bp"),
        ("DWV-A_6378F", "DWV-A_7259R", "~881 bp"), 
        ("DWV-A_8106F", "DWV-A_9010R", "~904 bp"),
        ("DWV-B_5612F", "DWV-B_6604R", "~992 bp"),
        ("DWV-B_7464F", "DWV-B_8406R", "~942 bp"),
        ("DWV-B_8376F", "DWV-B_9305R", "~929 bp"),
        ("ABPV_483F", "ABPV_1346R", "~863 bp"),
        ("ABPV_4327F", "ABPV_5171R", "~844 bp")
    ]
    
    print("\nRecommended primer pairs based on naming convention:")
    for forward, reverse, size in expected_pairs:
        if forward in primers and reverse in primers:
            f_seq = primers[forward]
            r_seq = primers[reverse]
            f_pos = extract_position_from_name(forward)
            r_pos = extract_position_from_name(reverse)
            calculated_size = r_pos - f_pos + len(r_seq) if f_pos and r_pos else "Unknown"
            
            print(f"\n{forward} + {reverse}")
            print(f"  Forward:  {f_seq} ({len(f_seq)} bp)")
            print(f"  Reverse:  {r_seq} ({len(r_seq)} bp)")
            print(f"  Expected: {size}")
            print(f"  Calculated: ~{calculated_size} bp")

def primer_compatibility_check():
    """Check primer compatibility within pairs"""
    print("\n4. PRIMER PAIR COMPATIBILITY")
    print("-" * 50)
    
    pairs_to_check = [
        ("DWV-A_5663F", "DWV-A_6662R"),
        ("DWV-A_6378F", "DWV-A_7259R"), 
        ("DWV-A_8106F", "DWV-A_9010R"),
        ("DWV-B_5612F", "DWV-B_6604R"),
        ("DWV-B_7464F", "DWV-B_8406R"),
        ("DWV-B_8376F", "DWV-B_9305R"),
        ("ABPV_483F", "ABPV_1346R"),
        ("ABPV_4327F", "ABPV_5171R")
    ]
    
    for forward, reverse in pairs_to_check:
        if forward in primers and reverse in primers:
            f_seq = primers[forward]
            r_seq = primers[reverse]
            f_tm = calculate_tm_basic(f_seq)
            r_tm = calculate_tm_basic(r_seq)
            tm_diff = abs(f_tm - r_tm)
            
            print(f"\n{forward} + {reverse}:")
            print(f"  Tm difference: {tm_diff}°C ({'Good' if tm_diff <= 5 else 'Check annealing temp'})")
            print(f"  Length diff: {abs(len(f_seq) - len(r_seq))} bp")

if __name__ == "__main__":
    analyze_primers()
    primer_compatibility_check()
    
    print("\n" + "=" * 80)
    print("NOTES:")
    print("- These are primers for bee virus detection (DWV-A, DWV-B, ABPV)")
    print("- Amplicon sizes are estimates based on primer positions in genome")
    print("- Actual sizes may vary depending on reference genome used")
    print("- For PCR optimization, consider primer annealing temperatures")
    print("=" * 80)