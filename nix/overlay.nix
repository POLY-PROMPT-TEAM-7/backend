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
          pydantic
          fastapi
          uvicorn
        ]) ++ (with prev; [
          python313Packages.study-ontology
        ]);
        doCheck = false;
      };
    };
  };
}