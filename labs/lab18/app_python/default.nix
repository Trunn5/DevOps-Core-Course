# Nix derivation for DevOps Info Service (FastAPI)
# This builds a reproducible Python application with exact dependencies
{ pkgs ? import <nixpkgs> {} }:

pkgs.python3Packages.buildPythonApplication {
  # Package metadata
  pname = "devops-info-service";
  version = "1.0.0";
  
  # Source code (current directory)
  src = ./.;
  
  # This tells Nix we don't have a setup.py - we'll install manually
  format = "other";
  
  # Python dependencies from requirements.txt
  # Note: Nix uses packages from nixpkgs, not PyPI directly
  # This provides stronger reproducibility guarantees
  propagatedBuildInputs = with pkgs.python3Packages; [
    fastapi              # Web framework
    uvicorn              # ASGI server
    prometheus-client    # Metrics
  ];
  
  # Build-time dependencies
  # makeWrapper allows us to wrap the Python script with the interpreter
  nativeBuildInputs = [ pkgs.makeWrapper ];
  
  # Installation phase - copy app and wrap it with Python
  installPhase = ''
    # Create bin directory in Nix store path
    mkdir -p $out/bin
    
    # Copy the application
    cp app.py $out/bin/devops-info-service
    
    # Make it executable
    chmod +x $out/bin/devops-info-service
    
    # Wrap with Python interpreter so it can execute
    # This ensures the app has access to all dependencies
    wrapProgram $out/bin/devops-info-service \
      --prefix PYTHONPATH : "$PYTHONPATH" \
      --set DATA_DIR "/tmp/devops-app-data"
  '';
  
  # Metadata
  meta = with pkgs.lib; {
    description = "DevOps Info Service - System information and health API";
    homepage = "https://github.com/yourusername/DevOps-Core-Course";
    license = licenses.mit;
    maintainers = [ ];
  };
}
