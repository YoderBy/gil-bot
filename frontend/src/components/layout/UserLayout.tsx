import React from 'react';
import { Outlet } from 'react-router-dom';

const UserLayout: React.FC = () => {
    return (
        <div>
            {/* Potentially add a header/navbar specific to user chat */}
            <main style={{ padding: '1rem' }}>
                <Outlet /> {/* User chat page will render here */}
            </main>
        </div>
    );
};

export default UserLayout; 