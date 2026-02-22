final: prev: {
  python313Packages = prev.python313Packages.override {
    overrides = pyFinal: pyPrev: {
      document-processor = pyFinal.buildPythonApplication rec {
        pname = "document_processor";
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
          python-dotenv
          python-docx
          python-pptx
        ]);
        doCheck = false;
      };
    };
  };
}
