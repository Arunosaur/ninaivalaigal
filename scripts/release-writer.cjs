module.exports = {
  transform(commit) {
    // Fix malformed commit dates from git history surgery (subtree/submodule imports)
    const d = commit.committerDate || commit.commitDate || commit.authorDate;
    try { 
      if (d && !isNaN(new Date(d).getTime())) return commit; 
    } catch (_) {}
    
    // Fallback: use current timestamp for commits with invalid dates
    commit.committerDate = new Date().toISOString();
    return commit;
  }
};
