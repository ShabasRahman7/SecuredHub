import { useState } from 'react';
import { Mail } from 'lucide-react';

const InviteModal = ({ isOpen, onClose, onInvite }) => {
  const [email, setEmail] = useState('');
  const [isInviting, setIsInviting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsInviting(true);
    const success = await onInvite(email);
    setIsInviting(false);
    
    if (success) {
      setEmail('');
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal modal-open">
      <div className="modal-box dark:bg-[#1a1d21] border dark:border-[#282f39]">
        <h3 className="font-bold text-lg mb-4">Invite Developer</h3>
        <form onSubmit={handleSubmit}>
          <div className="form-control mb-4">
            <label className="label">
              <span className="label-text">Email Address</span>
            </label>
            <input
              type="email"
              placeholder="developer@example.com"
              className="input input-bordered w-full dark:bg-[#101822] dark:border-[#282f39]"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isInviting}
              required
            />
            <label className="label">
              <span className="label-text-alt text-gray-500">
                An invitation email will be sent to this address
              </span>
            </label>
          </div>
          <div className="modal-action">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
              disabled={isInviting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="btn btn-primary bg-primary border-none"
              disabled={isInviting}
            >
              {isInviting ? (
                <>
                  <span className="loading loading-spinner loading-sm"></span>
                  Sending...
                </>
              ) : (
                <>
                  <Mail className="w-4 h-4" />
                  Send Invite
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InviteModal;
