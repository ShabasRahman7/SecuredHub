const EmptyState = ({ icon: Icon, title, description, action }) => {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4">
      {Icon && (
        <div className="bg-white/5 p-4 rounded-full">
          <Icon className="w-12 h-12 text-gray-600" />
        </div>
      )}
      {title && <p className="text-gray-400 text-lg font-medium">{title}</p>}
      {description && <p className="text-sm text-gray-500 text-center max-w-md">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

export default EmptyState;
