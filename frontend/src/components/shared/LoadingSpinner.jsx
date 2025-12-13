const LoadingSpinner = ({ size = 'lg', text = 'Loading...' }) => {
  const sizeClasses = {
    xs: 'loading-xs',
    sm: 'loading-sm',
    md: 'loading-md',
    lg: 'loading-lg',
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      <span className={`loading loading-spinner ${sizeClasses[size]} text-primary`}></span>
      {text && <p className="text-gray-400 text-sm">{text}</p>}
    </div>
  );
};

export default LoadingSpinner;
