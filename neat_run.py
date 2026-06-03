import sys
import neat
from car_env_neat import CarEnv


def run(config_path: str, track_name: str = "DriveIt_clean.png"):
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    env = CarEnv(track_name)

    population = neat.Population(config)
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    population.run(env.eval_genomes, 2000)


if __name__ == "__main__":
    track = sys.argv[1] if len(sys.argv) > 1 else "DriveIt_clean.png"
    run("config-feedforward.txt", track)
