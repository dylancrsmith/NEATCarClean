import neat
from car_env_neat import CarEnv


def run(config_path: str):
    # load config
    config = neat.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_path,
    )

    env = CarEnv()

    # create population
    population = neat.Population(config)

    # reporters
    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    # run for a big number of generations (you can stop manually)
    population.run(env.eval_genomes, 2000)


if __name__ == "__main__":
    run("config-feedforward.txt")
