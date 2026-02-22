{pkgs, lib, config, ...}: 
let 
  py = pkgs.python313Packages;
in {
  packages.default = py.backend-placeholder;
  devShells.default = pkgs.mkShell {
    packages = (with py; [
      backend-placeholder
      duckdb
      python
      flake8
      pip
    ]) ++ (with pkgs; [
      pyright
    ]);
  };
}