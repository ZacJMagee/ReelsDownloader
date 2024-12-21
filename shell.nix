{pkgs ? import <nixpkgs> {}}: let
  pythonPackages = pkgs.python3Packages;

  pyairtable = pythonPackages.buildPythonPackage rec {
    pname = "pyairtable";
    version = "2.2.0";
    format = "setuptools";
    src = pythonPackages.fetchPypi {
      inherit pname version;
      sha256 = "sha256-LTHHU4uYcwE4WKpmkW0dzdf6qLYA9YzBhR26nW957Tc=";
    };
    propagatedBuildInputs = with pythonPackages; [requests inflection pydantic];
    doCheck = false;
  };

  pythonWithPackages = pkgs.python3.withPackages (ps:
    with ps; [
      pyairtable
      google-auth-oauthlib
      google-auth-httplib2
      google-api-python-client
      requests
      python-lsp-server
      python-dotenv
    ]);
in
  pkgs.mkShell {
    buildInputs = with pkgs; [
      zsh
      pythonWithPackages
    ];

    shellHook = ''
      export ZDOTDIR="$HOME"
      export PYTHONPATH="$PWD:$PYTHONPATH"
      echo "Python development environment ready!"
      exec zsh
    '';
  }
