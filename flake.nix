{
  description = "Python project development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
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
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            zsh
            (python3.withPackages (ps: with ps; [
              pyairtable
              google-auth-oauthlib
              google-auth-httplib2
              google-api-python-client
              requests
              python-lsp-server
              python-dotenv
            ]))
          ];
          
          shellHook = ''
            export ZDOTDIR="$HOME"
            export PYTHONPATH="$PWD:$PYTHONPATH"
            echo "Python development environment ready!"
            exec zsh
          '';
        };
      });
}
