
from mpi4py import MPI
from repast4py.parameters import create_args_parser
from .hepb_model import run

if __name__ == "__main__":
    parser = create_args_parser()
    args = parser.parse_args()

    run(MPI.COMM_WORLD, args.parameters_file, args.parameters)

