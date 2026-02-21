{pkgs, lib, config, ...}: 
let 
  py = pkgs.python313Packages;
in {
  packages.docker = pkgs.dockerTools.buildImage {
    name = "backend-placeholder";
    tag = "latest";
    copyToRoot = pkgs.buildEnv {
      name = "image-root";
      paths = (with py; [
        backend-placeholder
      ]) ++ (with pkgs; [
        pkgs.cacert
      ]);
      pathsToLink = [
        "/bin"
        "/etc"
      ];
    };
    config = {
      Cmd = ["deploy-backend"];
      ExposedPorts = {"8000/tcp" = {};};
      Env = ["SSL_CERT_FILE=${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"];
    };
  };
}