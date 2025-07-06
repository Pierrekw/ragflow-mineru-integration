import React from 'react';
import ReactDOM from 'react-dom/client';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider, theme } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import dayjs from 'dayjs';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import relativeTime from 'dayjs/plugin/relativeTime';
import duration from 'dayjs/plugin/duration';
import timezone from 'dayjs/plugin/timezone';
import utc from 'dayjs/plugin/utc';

import { store } from './store';
import App from './App.tsx';
import './styles/index.css';

// 配置 dayjs 插件
dayjs.extend(relativeTime);
dayjs.extend(duration);
dayjs.extend(timezone);
dayjs.extend(utc);

// 设置默认语言
dayjs.locale('zh-cn');

// 获取用户语言偏好
const getLocale = () => {
  const savedLanguage = localStorage.getItem('language') as 'zh-CN' | 'en-US';
  return savedLanguage === 'en-US' ? enUS : zhCN;
};

// 获取主题配置
const getThemeConfig = () => {
  const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
  return {
    algorithm: savedTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      colorPrimary: '#1890ff',
      borderRadius: 6,
      wireframe: false,
    },
  };
};

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <ConfigProvider
          locale={getLocale()}
          theme={getThemeConfig()}
        >
          <App />
        </ConfigProvider>
      </BrowserRouter>
    </Provider>
  </React.StrictMode>
);

// 开发环境下的热更新支持
if (import.meta.hot) {
  import.meta.hot.accept();
}

// 全局错误处理
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error);
  // 这里可以添加错误上报逻辑
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason);
  // 这里可以添加错误上报逻辑
});

// 性能监控
if ('performance' in window) {
  window.addEventListener('load', () => {
    setTimeout(() => {
      const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      console.log('Page load time:', perfData.loadEventEnd - perfData.loadEventStart, 'ms');
    }, 0);
  });
}