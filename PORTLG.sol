
 // SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PORTLGuardLite {
    address public owner;
    bool public paused;

    event SecurityAlert(address indexed user, string action);
    event Paused(address indexed by);
    event Unpaused(address indexed by);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not authorized");
        _;
    }

    modifier whenNotPaused() {
        require(!paused, "Contract is paused");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function pause() external onlyOwner {
        require(!paused, "Already paused");
        paused = true;
        emit Paused(msg.sender);
    }

    function unpause() external onlyOwner {
        require(paused, "Not paused");
        paused = false;
        emit Unpaused(msg.sender);
    }

    function protectedAction() external whenNotPaused {
        emit SecurityAlert(
            msg.sender,
            "Protected action executed"
        );
    }
}

