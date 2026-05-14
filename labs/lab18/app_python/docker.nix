# Nix Docker image for DevOps Info Service
# This creates a reproducible Docker image using dockerTools
{ pkgs ? import <nixpkgs> {} }:

let
  # Import the application derivation from default.nix
  app = import ./default.nix { inherit pkgs; };
in
pkgs.dockerTools.buildLayeredImage {
  # Image name and tag
  name = "devops-info-service-nix";
  tag = "1.0.0";
  
  # Contents to include in the image
  # Only the app and its dependencies - no base image needed!
  contents = [ 
    app
    pkgs.coreutils  # Basic utilities like ls, cat, etc.
    pkgs.bash       # Shell for debugging
  ];
  
  # Container configuration
  config = {
    # Command to run when container starts
    Cmd = [ "${app}/bin/devops-info-service" ];
    
    # Exposed ports
    ExposedPorts = {
      "8080/tcp" = {};  # FastAPI default port
    };
    
    # Environment variables
    Env = [
      "DATA_DIR=/tmp/devops-app-data"
      "PYTHONUNBUFFERED=1"
    ];
    
    # Working directory
    WorkingDir = "/";
  };
  
  # CRITICAL: Fixed timestamp for reproducibility
  # Using "now" would create different hashes on each build!
  created = "1970-01-01T00:00:01Z";
}
