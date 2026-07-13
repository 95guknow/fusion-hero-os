// ALTE_Frau_95g - 10.000-Generationen-Evolutionsframework (Rust Prototype v0.2)
// Migration in progress - Performance optimized core loop

use std::collections::HashMap;

#[derive(Debug, Clone)]
struct Variant {
    id: u64,
    description: String,
    fitness: f64,
}

struct EvolutionFramework {
    current_generation: u64,
    memory: HashMap<u64, Variant>,
    best_variants: Vec<Variant>,
}

impl EvolutionFramework {
    fn new() -> Self {
        EvolutionFramework {
            current_generation: 0,
            memory: HashMap::new(),
            best_variants: Vec::new(),
        }
    }

    fn generate_variants(&self, count: usize) -> Vec<Variant> {
        (0..count)
            .map(|i| Variant {
                id: self.current_generation * 1000 + i as u64,
                description: format!("Mutation #{} in Gen {}", i, self.current_generation),
                fitness: 0.0,
            })
            .collect()
    }

    fn evaluate(&self, variants: &mut [Variant]) {
        for variant in variants.iter_mut() {
            // Simulated fitness calculation
            let base = ((variant.id as f64).sin().abs() * 0.6) + ((variant.id % 23) as f64 / 100.0);
            variant.fitness = base.min(1.0);
        }
    }

    fn select_best(&self, variants: &[Variant], top_n: usize) -> Vec<Variant> {
        let mut sorted = variants.to_vec();
        sorted.sort_by(|a, b| b.fitness.partial_cmp(&a.fitness).unwrap());
        sorted.into_iter().take(top_n).collect()
    }

    fn integrate(&mut self, selected: Vec<Variant>) {
        for variant in selected {
            self.memory.insert(variant.id, variant.clone());
            if self.best_variants.len() < 15 {
                self.best_variants.push(variant);
            }
        }
    }

    fn update_and_report(&mut self) {
        self.current_generation += 1;

        if self.current_generation % 100 == 0 {
            let best = self.best_variants.iter()
                .map(|v| v.fitness)
                .fold(0.0, f64::max);

            println!(
                "[Gen {:>5}] Best Fitness: {:.4} | Memory size: {}",
                self.current_generation, best, self.memory.len()
            );
        }
    }

    fn run(&mut self, total_generations: u64) {
        println!("=== ALTE_Frau_95g Rust Framework v0.2 ===");
        println!("Running {} generations...\n", total_generations);

        let start = std::time::Instant::now();

        for _ in 0..total_generations {
            let mut variants = self.generate_variants(24);
            self.evaluate(&mut variants);
            let selected = self.select_best(&variants, 5);
            self.integrate(selected);
            self.update_and_report();
        }

        let duration = start.elapsed();

        println!("\n=== Completed ===");
        println!("Generations: {}", self.current_generation);
        println!("Duration: {:?}", duration);
        println!("Best Fitness: {:.4}", 
            self.best_variants.iter().map(|v| v.fitness).fold(0.0, f64::max));
    }
}

fn main() {
    let mut framework = EvolutionFramework::new();
    framework.run(1000); // Test run with 1000 generations
}