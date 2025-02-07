import csv
from typing import List, Dict
from collections import Counter

def load_glass_data(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [{'location': row['location'], 
                 'length': int(row['glass_length']), 
                 'height': int(row['glass_height']), 
                 'qty': int(row['glass_qty'])} for row in reader]

def load_stock_sizes(filepath: str) -> List[Dict]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [{'length': int(row['length']), 
                 'width': int(row['width']), 
                 'qty': int(row['qty'])} for row in reader]

def expand_parts(glass_parts: List[Dict]) -> List[Dict]:
    expanded_parts = []
    for part in glass_parts:
        expanded_parts.extend([{'location': part['location'], 'length': part['length'], 'height': part['height']} for _ in range(part['qty'])])
    return expanded_parts

def calculate_layout(parts: List[Dict], stock_sizes: List[Dict], gap: int) -> List[Dict]:
    def can_fit(part, space):
        return (part['length'] <= space[2] and part['height'] <= space[3]) or \
               (part['height'] <= space[2] and part['length'] <= space[3])

    def place_part(part, position, rotated):
        return {'part': part, 'position': position, 'rotated': rotated}

    sheets = []
    remaining_parts = parts.copy()

    while remaining_parts:
        best_utilization = 0
        best_sheet = None
        best_placement = None

        for stock in stock_sizes:
            sheet = {'size': (stock['length'], stock['width']), 'placements': []}
            available_space = [(0, 0, stock['length'], stock['width'])]

            for part in remaining_parts:
                best_fit = None
                for i, space in enumerate(available_space):
                    if can_fit(part, space):
                        rotated = part['height'] <= space[2] and part['length'] > space[2]
                        best_fit = (i, space, rotated)
                        break

                if best_fit:
                    i, space, rotated = best_fit
                    x, y = space[0], space[1]
                    w, h = (part['height'], part['length']) if rotated else (part['length'], part['height'])
                    sheet['placements'].append(place_part(part, (x, y), rotated))
                    
                    # Update available space
                    del available_space[i]
                    if x + w + gap < stock['length']:
                        available_space.append((x + w + gap, y, stock['length'] - (x + w + gap), h))
                    if y + h + gap < stock['width']:
                        available_space.append((x, y + h + gap, w, stock['width'] - (y + h + gap)))
                    available_space.sort(key=lambda s: (s[2] * s[3], s[2] + s[3]), reverse=True)

            utilization = sum(p['part']['length'] * p['part']['height'] for p in sheet['placements']) / (stock['length'] * stock['width'])
            if utilization > best_utilization:
                best_utilization = utilization
                best_sheet = sheet
                best_placement = [p['part'] for p in sheet['placements']]

        if best_sheet:
            sheets.append(best_sheet)
            for part in best_placement:
                remaining_parts.remove(part)
        else:
            # If no placement found, add the smallest part to a new sheet
            smallest_part = min(remaining_parts, key=lambda p: p['length'] * p['height'])
            smallest_stock = min(stock_sizes, key=lambda s: s['length'] * s['width'])
            sheets.append({
                'size': (smallest_stock['length'], smallest_stock['width']),
                'placements': [place_part(smallest_part, (0, 0), False)]
            })
            remaining_parts.remove(smallest_part)

    return sheets

def optimize_glass_cutting(glass_data_file: str, stock_sizes_file: str, gap: int):
    glass_parts = load_glass_data(glass_data_file)
    stock_sizes = load_stock_sizes(stock_sizes_file)
    
    # Expand parts based on quantity
    expanded_parts = expand_parts(glass_parts)
    
    # Sort parts by area in descending order
    expanded_parts.sort(key=lambda x: x['length'] * x['height'], reverse=True)
    
    optimized_layout = calculate_layout(expanded_parts, stock_sizes, gap)
    
    # Calculate total areas in square millimeters
    total_glass_area_mm2 = sum(part['length'] * part['height'] for part in expanded_parts)
    total_sheet_area_mm2 = sum(sheet['size'][0] * sheet['size'][1] for sheet in optimized_layout)
    
    # Convert areas to square meters
    total_glass_area_m2 = total_glass_area_mm2 / 1_000_000  # 1 m² = 1,000,000 mm²
    total_sheet_area_m2 = total_sheet_area_mm2 / 1_000_000  # 1 m² = 1,000,000 mm²
    
    # Calculate efficiency and wastage
    used_area_percentage = (total_glass_area_mm2 / total_sheet_area_mm2) * 100
    wastage_percentage = 100 - used_area_percentage
    
    # Calculate sheet size usage summary
    sheet_counter = Counter((sheet['size'][0], sheet['size'][1]) for sheet in optimized_layout)
    
    # Print results 
    print(f"\nTotal sheets used: {len(optimized_layout)}")
    print(f"\nTotal glass area: {total_glass_area_m2:.3f} sq m")
    print(f"Total stock area used: {total_sheet_area_m2:.3f} sq m")
    print(f"\nUsed area percentage: {used_area_percentage:.2f}%")
    print(f"Wastage percentage: {wastage_percentage:.2f}%")
    
    # Print summary of sheet sizes used and their quantity
    print("\nSummary of sheet sizes used:")
    for (length, width), qty in sheet_counter.items():
        print(f"  {length}mm x {width}mm: {qty} pcs")
    
    print("Optimized Layout:")
    for i, sheet in enumerate(optimized_layout, 1):
        print(f"Sheet {i}: {sheet['size'][0]}mm x {sheet['size'][1]}mm")
        for placement in sheet['placements']:
            part = placement['part']
            position = placement['position']
            orientation = "height as length" if placement['rotated'] else "normal"
            print(f"  {part['location']} ({part['length']}x{part['height']}) at position {position} ({orientation})")

# Example usage
glass_data_file = 'cutlist/glass_data.csv'
stock_sizes_file = 'cutlist/glass_sheet_size.csv'
gap = 0  # Gap between parts in mm

optimize_glass_cutting(glass_data_file, stock_sizes_file, gap)
