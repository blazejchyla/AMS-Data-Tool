from PyInstaller.utils.hooks import copy_metadata

# include duckdb's metadata in the build
datas = copy_metadata('duckdb')