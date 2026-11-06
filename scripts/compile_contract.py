"""Compile contracts/PORTLGuardLite.sol into build/PORTLGuardLite.json."""
import json
from pathlib import Path
import solcx
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"contracts"/"PORTLGuardLite.sol"
BUILD=ROOT/"build"
SOLC_VERSION="0.8.24"
def compile_contract():
    if not SOURCE.is_file(): raise FileNotFoundError(SOURCE)
    solcx.install_solc(SOLC_VERSION)
    result=solcx.compile_files([str(SOURCE)],output_values=["abi","bin"],solc_version=SOLC_VERSION)
    _,data=next(iter(result.items()))
    BUILD.mkdir(exist_ok=True)
    out=BUILD/"PORTLGuardLite.json"
    out.write_text(json.dumps({"abi":data["abi"],"bytecode":data["bin"]},indent=2))
    return out
if __name__=="__main__": print("Wrote",compile_contract())
