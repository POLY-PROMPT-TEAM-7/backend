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
          langchain-core
          langchain-openai
          langgraph
          python-dotenv
          pdfplumber
        ]);
        doCheck = false;
      };
    };
  };
}