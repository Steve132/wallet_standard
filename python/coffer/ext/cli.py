import taxes
import forks

def load_cli_exts_subparsers(extsubparsers,parents_available):
	taxes.load_cli_subparsers(extsubparsers,parents_available)
	forks.load_cli_subparsers(extsubparsers,parents_available)
