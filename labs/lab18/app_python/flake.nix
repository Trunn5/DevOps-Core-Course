{
  description = "DevOps Info Service - Reproducible Build with Nix Flakes";

  # Input: Pinned nixpkgs for reproducibility
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-24.11";
  };

  outputs = { self, nixpkgs }:
    let
      # System architecture
      # macOS: use "x86_64-darwin" for Intel or "aarch64-darwin" for M1/M2/M3
      # Linux: use "x86_64-linux"
      # Change this based on your system!
      system = "aarch64-darwin";  # Change if needed
      
      pkgs = nixpkgs.legacyPackages.${system};
    in
    {
      # Packages that can be built
      packages.${system} = {
        # Default package - the FastAPI application
        default = import ./default.nix { inherit pkgs; };
        
        # Docker image package
        dockerImage = import ./docker.nix { inherit pkgs; };
      };

      # Development shell with all dependencies
      # Enter with: nix develop
      devShells.${system}.default = pkgs.mkShell {
        buildInputs = with pkgs; [
          python313
          python313Packages.fastapi
          python313Packages.uvicorn
          python313Packages.prometheus-client
        ];
        
        shellHook = ''
          echo "🚀 DevOps Info Service - Development Environment"
          echo "Python version: $(python --version)"
          echo ""
          echo "Available commands:"
          echo "  python app.py          - Run the application"
          echo "  nix build              - Build with Nix"
          echo "  nix build .#dockerImage - Build Docker image"
          echo ""
        '';
      };

      # Apps that can be run directly with 'nix run'
      apps.${system}.default = {
        type = "app";
        program = "${self.packages.${system}.default}/bin/devops-info-service";
      };
    };
}
