final: prev: {
  python313Packages = prev.python313Packages.override {
    overrides = pyFinal: pyPrev: {
      backend-placeholder = pyFinal.buildPythonApplication rec {
        pname = "backend_placeholder";
        version = "1.0.0";
        format = "pyproject";
        src = ../.;
        build-system = with pyFinal; [
          setuptools
          wheel
        ];
        propagatedBuildInputs = (with pyFinal; [
          boto3
          pydantic
          fastapi
          uvicorn
          python-multipart
        ]);
        doCheck = false;
      };
    };
  };
}