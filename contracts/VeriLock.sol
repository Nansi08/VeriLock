// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract VeriLock {
    struct Document {
        bool isVerified;
        address uploader;
    }

    mapping(string => Document) private documents;

    event DocumentUploaded(string docHash, address uploader);
    event DocumentVerified(string docHash, bool verified);

    constructor() {}

    function uploadDocument(string memory docHash) public {
        require(bytes(docHash).length > 0, "Invalid hash");
        require(documents[docHash].uploader == address(0), "Document already uploaded");
        documents[docHash] = Document(false, msg.sender);
        emit DocumentUploaded(docHash, msg.sender);
    }

    function verifyDocument(string memory docHash) public {
        require(bytes(docHash).length > 0, "Invalid hash");
        require(documents[docHash].uploader != address(0), "Document not found");
        documents[docHash].isVerified = true;
        emit DocumentVerified(docHash, true);
    }

    function isDocumentVerified(string memory docHash) public view returns (bool) {
        require(bytes(docHash).length > 0, "Invalid hash");
        return documents[docHash].isVerified;
    }

    function getUploader(string memory docHash) public view returns (address) {
        return documents[docHash].uploader;
    }
}
