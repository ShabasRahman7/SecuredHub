import Swal from 'sweetalert2';

const commonConfig = {
    background: '#0A0F16',
    color: '#fff',
    confirmButtonColor: '#3B82F6', // Primary Blue
    cancelButtonColor: '#1F2937', // Dark Gray
    customClass: {
        popup: 'border border-gray-800 rounded-xl',
        title: 'text-xl font-bold text-white',
        htmlContainer: 'text-gray-400',
        confirmButton: 'px-6 py-2.5 rounded-lg font-medium text-sm transition-colors',
        cancelButton: 'px-6 py-2.5 rounded-lg font-medium text-sm text-gray-400 hover:text-white transition-colors',
        actions: 'gap-3'
    },
    buttonsStyling: false
};

export const showConfirmDialog = async ({
    title = 'Are you sure?',
    text = "You won't be able to revert this!",
    confirmButtonText = 'Yes, delete it!',
    cancelButtonText = 'Cancel',
    icon = 'warning'
}) => {
    const result = await Swal.fire({
        ...commonConfig,
        title,
        text,
        icon,
        showCancelButton: true,
        confirmButtonText,
        cancelButtonText,
        reverseButtons: true
    });

    return result.isConfirmed;
};

export const showSuccessToast = (title) => {
    Swal.fire({
        ...commonConfig,
        title,
        icon: 'success',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
};

export const showErrorToast = (title) => {
    Swal.fire({
        ...commonConfig,
        title,
        icon: 'error',
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3000,
        timerProgressBar: true
    });
};
