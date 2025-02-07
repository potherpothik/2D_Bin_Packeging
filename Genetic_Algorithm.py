import csv
import random
from typing import List, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages

@dataclass
class Part:
    location: str
    length: int
    height: int
    quantity: int

@dataclass
class Placement:
    part: Part
    x: int
    y: int
    rotated: bool

class Sheet:
    def __init__(self, length: int, width: int):
        self.length = length
        self.width = width
        self.placements: List[Placement] = []
        self.remaining_space = [(0, 0, length, width)]

    def add_part(self, part: Part, x: int, y: int, rotated: bool):
        actual_length = part.height if rotated else part.length
        actual_height = part.length if rotated else part.height
        self.placements.append(Placement(part, x, y, rotated))

        # Update remaining space after placing the part
        new_remaining = []
        for space in self.remaining_space:
            sx, sy, sl, sh = space
            if x < sx + sl and y < sy + sh:
                if y > sy:
                    new_remaining.append((sx, sy, sl, y - sy))
                if y + actual_height < sy + sh:
                    new_remaining.append((sx, y + actual_height, sl, sy + sh - (y + actual_height)))
                if x > sx:
                    new_remaining.append((sx, max(sy, y), x - sx, min(sh, actual_height)))
                if x + actual_length < sx + sl:
                    new_remaining.append((x + actual_length, max(sy, y), sx + sl - (x + actual_length), min(sh, actual_height)))
            else:
                new_remaining.append(space)
        self.remaining_space = new_remaining

def load_glass_data(filepath: str) -> List[Part]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [Part(row['location'], int(row['glass_length']), int(row['glass_height']), int(row['glass_qty'])) for row in reader]

def load_stock_sizes(filepath: str) -> List[Tuple[int, int]]:
    with open(filepath, 'r') as file:
        reader = csv.DictReader(file)
        return [(int(row['length']), int(row['width'])) for row in reader]

def find_best_fit(sheet: Sheet, part: Part) -> Tuple[int, int, bool]:
    best_fit = None
    min_waste = float('inf')
    
    for space in sheet.remaining_space:
        x, y, w, h = space
        for rotated in (False, True):
            pl, ph = (part.height, part.length) if rotated else (part.length, part.height)
            if pl <= w and ph <= h:
                waste = w * h - pl * ph
                if waste < min_waste:
                    min_waste = waste
                    best_fit = (x, y, rotated)
    
    return best_fit if best_fit else (-1, -1, False)

def genetic_heuristic_optimization(parts: List[Part], stock_sizes: List[Tuple[int, int]], population_size: int = 5, generations: int = 20) -> List[Sheet]:
    def initialize_population():
        population = []
        for _ in range(population_size):
            layout = optimize_cutting_heuristic(parts.copy(), stock_sizes)
            population.append(layout)
        return population

    def fitness(sheets: List[Sheet]) -> float:
        total_sheet_area = sum(sheet.length * sheet.width for sheet in sheets)
        used_area = sum(
            placement.part.length * placement.part.height
            for sheet in sheets
            for placement in sheet.placements
        )
        return used_area / total_sheet_area if total_sheet_area > 0 else 0

    def crossover(parent1: List[Sheet], parent2: List[Sheet]) -> List[Sheet]:
        split = len(parent1) // 2
        child = parent1[:split] + parent2[split:]
        return child

    def mutate(sheets: List[Sheet]):
        if sheets:
            random_sheet = random.choice(sheets)
            if random_sheet.placements:
                random_sheet.placements.pop(random.randint(0, len(random_sheet.placements) - 1))

    population = initialize_population()

    for generation in range(generations):
        population.sort(key=fitness, reverse=True)
        best_fitness = fitness(population[0])

        print(f"Generation {generation + 1}, Best Fitness: {best_fitness:.4f}")

        next_generation = population[:1]

        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(population[:3], 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.1:
                mutate(child)
            next_generation.append(child)

        population = next_generation

        if len(next_generation) > 1 and fitness(next_generation[0]) == best_fitness:
            print("Early stopping triggered: no improvement in fitness.")
            break

    return max(population, key=fitness)

def optimize_cutting_heuristic(parts: List[Part], stock_sizes: List[Tuple[int, int]]) -> List[Sheet]:
    sheets = []
    parts.sort(key=lambda p: p.length * p.height, reverse=True)
    
    while parts:
        sheet = Sheet(*stock_sizes[0])
        for part in parts[:]:
            for _ in range(part.quantity):
                x, y, rotated = find_best_fit(sheet, part)
                if x != -1:
                    sheet.add_part(part, x, y, rotated)
                    part.quantity -= 1
                    if part.quantity == 0:
                        parts.remove(part)
        sheets.append(sheet)
    return sheets

def visualize_sheets(sheets: List[Sheet], output_pdf: str):
    with PdfPages(output_pdf) as pdf:
        for i, sheet in enumerate(sheets):
            fig, ax = plt.subplots(figsize=(8, 6))
            ax.set_xlim(0, sheet.length)
            ax.set_ylim(0, sheet.width)
            ax.set_title(f"Sheet {i + 1}: {sheet.length}x{sheet.width}")
            for placement in sheet.placements:
                color = f"#{random.randint(0, 0xFFFFFF):06x}"
                actual_length = placement.part.height if placement.rotated else placement.part.length
                actual_height = placement.part.length if placement.rotated else placement.part.height
                rect = Rectangle((placement.x, placement.y), actual_length, actual_height, edgecolor="black", facecolor=color, alpha=0.7)
                ax.add_patch(rect)
                ax.text(placement.x + actual_length / 2, placement.y + actual_height / 2, placement.part.location,
                        ha="center", va="center", fontsize=8, color="white")
            pdf.savefig(fig)
            plt.close()

def main():
    # File paths
    glass_data_file = 'glass_data.csv'
    stock_sizes_file = 'glass_sheet_size.csv'

    parts = load_glass_data(glass_data_file)
    stock_sizes = load_stock_sizes(stock_sizes_file)

    optimized_layout = genetic_heuristic_optimization(parts, stock_sizes)
    visualize_sheets(optimized_layout, "optimized_layout.pdf")
    print("Optimization complete. Results saved to 'optimized_layout.pdf'.")

if __name__ == "__main__":
    main()
