{
  description = "backend placeholder (1.0.0)";
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    systems.url = "github:nix-systems/default";
    flake-parts.url = "github:hercules-ci/flake-parts";
    study-ontology.url = "github:POLY-PROMPT-TEAM-7/StudyOntology";
  };
  outputs = inputs @ {self, systems, nixpkgs, flake-parts, study-ontology, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      systems = import inputs.systems;
      perSystem = {pkgs, lib, config, system, ...}: {
        _module.args.pkgs = import nixpkgs {
          inherit system;
          overlays = [
            study-ontology.overlays.default
            self.overlays.default
          ];
        };
        imports = [
          ./nix/shell.nix
        ];
      };
      flake = {
        overlays.default = import ./nix/overlay.nix;
      };
    };
}