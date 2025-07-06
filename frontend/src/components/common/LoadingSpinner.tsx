import React from 'react';
import { Spin, SpinProps } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

interface LoadingSpinnerProps extends SpinProps {
  tip?: string;
  overlay?: boolean;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  tip = '加载中...',
  overlay = false,
  size = 'default',
  ...props
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: 24 }} spin />;

  const spinner = (
    <Spin
      indicator={antIcon}
      tip={tip}
      size={size}
      {...props}
    />
  );

  if (overlay) {
    return (
      <div className="fixed inset-0 bg-white bg-opacity-75 flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default LoadingSpinner;