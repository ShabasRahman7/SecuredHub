import { useState, useEffect } from 'react';

const AssignDevsModal = ({ isOpen, onClose, onAssign, members, selectedRepo }) => {
  const [selectedDevs, setSelectedDevs] = useState([]);

  useEffect(() => {
    if (isOpen) {
      setSelectedDevs([]);
    }
  }, [isOpen]);

  const handleSubmit = async () => {
    if (!selectedRepo) return;
    const success = await onAssign(selectedRepo.id, selectedDevs);
    
    if (success) {
      setSelectedDevs([]);
      onClose();
    }
  };

  if (!isOpen) return null;

  const developers = members.filter(m => m.role === 'developer');

  return (
    <div className="modal modal-open">
      <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
        <h3 className="font-bold text-lg mb-4">Assign Developers</h3>
        <p className="text-sm text-gray-500 mb-4">
          Repository: <span className="font-medium text-white">{selectedRepo?.name}</span>
        </p>
        <div className="flex flex-col gap-2 mb-4 max-h-64 overflow-y-auto">
          {developers.length > 0 ? (
            developers.map((m) => (
              <label
                key={m.id}
                className="label cursor-pointer justify-start gap-4 hover:bg-white/5 p-2 rounded"
              >
                <input
                  type="checkbox"
                  className="checkbox checkbox-primary"
                  checked={selectedDevs.includes(m.user?.id || m.id)}
                  onChange={(e) => {
                    const devId = m.user?.id || m.id;
                    if (e.target.checked) {
                      setSelectedDevs([...selectedDevs, devId]);
                    } else {
                      setSelectedDevs(selectedDevs.filter((id) => id !== devId));
                    }
                  }}
                />
                <span>
                  {m.first_name} {m.last_name}
                </span>
              </label>
            ))
          ) : (
            <p className="text-center text-gray-500 py-4">
              No developers available. Invite developers first.
            </p>
          )}
        </div>
        <div className="modal-action">
          <button type="button" className="btn btn-ghost" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary bg-primary border-none"
            onClick={handleSubmit}
            disabled={selectedDevs.length === 0}
          >
            Save
          </button>
        </div>
      </div>
    </div>
  );
};

export default AssignDevsModal;
