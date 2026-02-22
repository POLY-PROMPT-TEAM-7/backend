final: prev: {
  python313Packages = prev.python313Packages.override {
    overrides = pyFinal: pyPrev: {
      textract = pyFinal.buildPythonPackage rec {
        pname = "textract";
        version = "1.6.5";
        format = "setuptools";
        src = pyPrev.fetchPypi {
          inherit pname version;
          sha256 = "sha256-aPDwkFaIWCHmxD2FOJh1GNqpQFfDBmefKFfMXuZq2FA="; 
        };
        build-system = (with pyFinal; [
          setuptools
          wheel
        ]);
        postPatch = ''
          sed -E -i 's/[=<>~!].*//g' requirements/python
          substituteInPlace textract/parsers/pdf_parser.py --replace-fail "pdf2txt.py" "pdf2txt"
        '';
        propagatedBuildInputs = (with pyFinal; [
          speechrecognition
          beautifulsoup4
          pdfminer-six
          argcomplete
          python-pptx
          python-docx
          extract-msg
          docx2txt
          ebooklib
          chardet
          xlrd
          six
        ]);
        doCheck = false;
      };
      backend-placeholder = pyFinal.buildPythonApplication rec {
        pname = "backend_placeholder";
        version = "1.0.0";
        format = "pyproject";
        src = ../.;
        build-system = (with pyFinal; [
          setuptools
          wheel
        ]);
        propagatedBuildInputs = (with pyFinal; [
          langchain-openai
          python-multipart
          langchain-core
          pdfminer-six
          langchain
          langgraph
          textract
          requests
          pydantic
          fastapi
          uvicorn
          duckdb
          httpx
        ]) ++ (with prev.python313Packages; [
          study-ontology
        ]);
        doCheck = false;
      };
    };
  };
}