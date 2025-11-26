import { useState } from 'react';

const AddRepoModal = ({ isOpen, onClose, onAdd }) => {
  const [repoData, setRepoData] = useState({
    name: '',
    url: '',
    visibility: 'private',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await onAdd(repoData);
    
    if (success) {
      setRepoData({ name: '', url: '', visibility: 'private' });
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
        <h3 className="font-bold text-lg mb-4">Connect Repository</h3>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <input
            type="text"
            placeholder="Repository Name"
            className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]"
            value={repoData.name}
            onChange={(e) => setRepoData({ ...repoData, name: e.target.value })}
            required
          />
          <input
            type="url"
            placeholder="Repository URL (HTTPS)"
            className="input input-bordered dark:bg-[#101822] dark:border-[#282f39]"
            value={repoData.url}
            onChange={(e) => setRepoData({ ...repoData, url: e.target.value })}
            required
          />
          <select
            className="select select-bordered dark:bg-[#101822] dark:border-[#282f39]"
            value={repoData.visibility}
            onChange={(e) => setRepoData({ ...repoData, visibility: e.target.value })}
          >
            <option value="private">Private</option>
            <option value="public">Public</option>
          </select>
          <div className="modal-action">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary bg-primary border-none">
              Connect
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddRepoModal;
