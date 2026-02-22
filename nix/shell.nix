{pkgs, lib, config, ...}: 
let 
  py = pkgs.python313Packages;
in {
  packages.default = py.document-processor;
  devShells.default = pkgs.mkShell {
    packages = (with py; [
      backend-placeholder
      duckdb
      python
      pytest
      flake8
    ]) ++ (with pkgs; [
      pyright
    ]);
   };
}
