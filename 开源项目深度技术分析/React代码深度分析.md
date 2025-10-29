# React代码深度分析文档

## 项目概述

React是一个用于构建用户界面的JavaScript库，由Facebook开发并开源。它采用组件化开发模式，支持虚拟DOM、单向数据流、JSX语法等特性，是现代前端开发的核心技术之一。

## 项目结构分析

### 核心模块结构
```
react/
├── packages/
│   ├── react/                    # React核心
│   │   ├── src/
│   │   │   ├── React.js          # React主入口
│   │   │   ├── ReactBaseClasses.js # 基础类
│   │   │   ├── ReactChildren.js   # 子元素处理
│   │   │   ├── ReactElement.js    # React元素
│   │   │   └── ...
│   │   └── package.json
│   ├── react-dom/                # DOM渲染
│   │   ├── src/
│   │   │   ├── client/
│   │   │   │   ├── ReactDOM.js    # DOM渲染入口
│   │   │   │   ├── ReactDOMRoot.js # React根节点
│   │   │   │   └── ...
│   │   │   └── server/
│   │   │       └── ReactDOMServer.js # 服务端渲染
│   │   └── package.json
│   ├── react-reconciler/         # 协调器
│   │   ├── src/
│   │   │   ├── ReactFiber.js      # Fiber架构
│   │   │   ├── ReactFiberReconciler.js # 协调器
│   │   │   └── ...
│   │   └── package.json
│   ├── scheduler/                # 调度器
│   │   ├── src/
│   │   │   ├── Scheduler.js       # 调度器
│   │   │   ├── SchedulerPriorities.js # 优先级
│   │   │   └── ...
│   │   └── package.json
│   └── ...
└── ...
```

### 主要代码文件分析

#### 1. React核心模块 (react/src/)
- **React.js**: React库的主入口文件
- **ReactBaseClasses.js**: Component和PureComponent基类
- **ReactElement.js**: React元素创建和验证
- **ReactChildren.js**: 子元素遍历和处理

#### 2. DOM渲染模块 (react-dom/src/)
- **ReactDOM.js**: DOM渲染器主入口
- **ReactDOMRoot.js**: React 18+的根节点API
- **ReactDOMServer.js**: 服务端渲染

#### 3. 协调器模块 (react-reconciler/src/)
- **ReactFiber.js**: Fiber节点定义和操作
- **ReactFiberReconciler.js**: 协调器实现
- **ReactFiberHooks.js**: Hooks实现

#### 4. 调度器模块 (scheduler/src/)
- **Scheduler.js**: 任务调度器
- **SchedulerPriorities.js**: 任务优先级定义
- **SchedulerMinHeap.js**: 最小堆数据结构

## 接口分析

### 1. 组件接口

#### 函数组件
```javascript
import React, { useState, useEffect, useCallback, useMemo } from 'react';

// 基础函数组件
function Welcome(props) {
  return <h1>Hello, {props.name}</h1>;
}

// 使用Hooks的函数组件
function UserProfile({ userId }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 副作用处理
  useEffect(() => {
    const fetchUser = async () => {
      try {
        setLoading(true);
        const response = await fetch(`/api/users/${userId}`);
        const userData = await response.json();
        setUser(userData);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUser();
  }, [userId]); // 依赖数组

  // 记忆化回调
  const handleUpdate = useCallback((updatedUser) => {
    setUser(updatedUser);
  }, []);

  // 记忆化计算
  const userInfo = useMemo(() => {
    if (!user) return null;
    return {
      fullName: `${user.firstName} ${user.lastName}`,
      age: new Date().getFullYear() - new Date(user.birthDate).getFullYear()
    };
  }, [user]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>User not found</div>;

  return (
    <div className="user-profile">
      <h2>{userInfo.fullName}</h2>
      <p>Age: {userInfo.age}</p>
      <p>Email: {user.email}</p>
      <button onClick={() => handleUpdate({ ...user, name: 'Updated Name' })}>
        Update User
      </button>
    </div>
  );
}

// 使用React.memo优化性能
const MemoizedUserProfile = React.memo(UserProfile);
```

#### 类组件
```javascript
import React, { Component } from 'react';

// 基础类组件
class Welcome extends Component {
  render() {
    return <h1>Hello, {this.props.name}</h1>;
  }
}

// 完整类组件
class UserProfile extends Component {
  constructor(props) {
    super(props);
    this.state = {
      user: null,
      loading: true,
      error: null
    };
    
    // 绑定方法
    this.handleUpdate = this.handleUpdate.bind(this);
    this.fetchUser = this.fetchUser.bind(this);
  }

  componentDidMount() {
    this.fetchUser();
  }

  componentDidUpdate(prevProps) {
    if (prevProps.userId !== this.props.userId) {
      this.fetchUser();
    }
  }

  componentWillUnmount() {
    // 清理操作
    if (this.controller) {
      this.controller.abort();
    }
  }

  async fetchUser() {
    try {
      this.setState({ loading: true, error: null });
      
      this.controller = new AbortController();
      const response = await fetch(`/api/users/${this.props.userId}`, {
        signal: this.controller.signal
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch user');
      }
      
      const userData = await response.json();
      this.setState({ user: userData, loading: false });
    } catch (error) {
      if (error.name !== 'AbortError') {
        this.setState({ error: error.message, loading: false });
      }
    }
  }

  handleUpdate(updatedUser) {
    this.setState({ user: updatedUser });
  }

  render() {
    const { user, loading, error } = this.state;

    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!user) return <div>User not found</div>;

    return (
      <div className="user-profile">
        <h2>{user.name}</h2>
        <p>Email: {user.email}</p>
        <p>Role: {user.role}</p>
        <button onClick={() => this.handleUpdate({ ...user, name: 'Updated Name' })}>
          Update User
        </button>
      </div>
    );
  }
}

// 使用PureComponent优化性能
class OptimizedUserProfile extends React.PureComponent {
  // 浅比较props和state
}
```

#### 高阶组件
```javascript
import React from 'react';

// 基础高阶组件：添加加载状态
function withLoading(WrappedComponent) {
  return function WithLoadingComponent(props) {
    const [loading, setLoading] = React.useState(true);
    const [data, setData] = React.useState(null);

    React.useEffect(() => {
      const fetchData = async () => {
        setLoading(true);
        try {
          // 模拟数据获取
          const result = await props.fetchData();
          setData(result);
        } catch (error) {
          console.error('Error fetching data:', error);
        } finally {
          setLoading(false);
        }
      };

      fetchData();
    }, [props.fetchData]);

    if (loading) {
      return <div>Loading...</div>;
    }

    return <WrappedComponent {...props} data={data} />;
  };
}

// 使用高阶组件
function UserList({ data }) {
  return (
    <ul>
      {data.map(user => (
        <li key={user.id}>{user.name}</li>
      ))}
    </ul>
  );
}

const UserListWithLoading = withLoading(UserList);

// 渲染高阶组件
function App() {
  const fetchUsers = async () => {
    const response = await fetch('/api/users');
    return response.json();
  };

  return <UserListWithLoading fetchData={fetchUsers} />;
}

// 组合多个高阶组件
import { compose } from 'redux';

const withAuth = (WrappedComponent) => {
  return function WithAuthComponent(props) {
    const [authenticated, setAuthenticated] = React.useState(false);
    
    React.useEffect(() => {
      // 检查认证状态
      const checkAuth = async () => {
        const token = localStorage.getItem('token');
        setAuthenticated(!!token);
      };
      
      checkAuth();
    }, []);

    if (!authenticated) {
      return <div>Please log in</div>;
    }

    return <WrappedComponent {...props} />;
  };
};

const EnhancedComponent = compose(
  withAuth,
  withLoading
)(UserList);
```

#### 自定义Hooks
```javascript
import { useState, useEffect, useCallback } from 'react';

// 自定义Hook：数据获取
function useFetch(url, options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(url, options);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [url, options]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// 自定义Hook：本地存储
function useLocalStorage(key, initialValue) {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = window.localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      window.localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error(`Error setting localStorage key "${key}":`, error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
}

// 自定义Hook：表单处理
function useForm(initialValues = {}, validate) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});

  const handleChange = useCallback((event) => {
    const { name, value, type, checked } = event.target;
    
    setValues(prevValues => ({
      ...prevValues,
      [name]: type === 'checkbox' ? checked : value
    }));

    // 实时验证
    if (validate) {
      setErrors(prevErrors => ({
        ...prevErrors,
        [name]: validate(name, value)
      }));
    }
  }, [validate]);

  const handleBlur = useCallback((event) => {
    const { name } = event.target;
    setTouched(prevTouched => ({
      ...prevTouched,
      [name]: true
    }));
  }, []);

  const handleSubmit = useCallback((onSubmit) => (event) => {
    event.preventDefault();
    
    // 最终验证
    if (validate) {
      const newErrors = {};
      Object.keys(values).forEach(key => {
        newErrors[key] = validate(key, values[key]);
      });
      setErrors(newErrors);
      
      // 检查是否有错误
      const hasErrors = Object.values(newErrors).some(error => error);
      if (hasErrors) return;
    }
    
    onSubmit(values);
  }, [values, validate]);

  const resetForm = useCallback(() => {
    setValues(initialValues);
    setErrors({});
    setTouched({});
  }, [initialValues]);

  return {
    values,
    errors,
    touched,
    handleChange,
    handleBlur,
    handleSubmit,
    resetForm
  };
}

// 使用自定义Hooks
function UserForm() {
  const { data: user, loading, error } = useFetch('/api/user/1');
  const [theme, setTheme] = useLocalStorage('theme', 'light');
  
  const form = useForm({
    name: '',
    email: '',
    age: ''
  }, (name, value) => {
    // 验证规则
    switch (name) {
      case 'name':
        return value.length < 2 ? 'Name must be at least 2 characters' : '';
      case 'email':
        return !/\S+@\S+\.\S+/.test(value) ? 'Invalid email address' : '';
      case 'age':
        return value < 0 || value > 150 ? 'Age must be between 0 and 150' : '';
      default:
        return '';
    }
  });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  const handleSubmit = (formData) => {
    console.log('Form submitted:', formData);
    // 提交表单数据
  };

  return (
    <div className={`app ${theme}`}>
      <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>
        Toggle Theme
      </button>
      
      <form onSubmit={form.handleSubmit(handleSubmit)}>
        <div>
          <label>Name:</label>
          <input
            type="text"
            name="name"
            value={form.values.name}
            onChange={form.handleChange}
            onBlur={form.handleBlur}
          />
          {form.touched.name && form.errors.name && (
            <span className="error">{form.errors.name}</span>
          )}
        </div>
        
        <div>
          <label>Email:</label>
          <input
            type="email"
            name="email"
            value={form.values.email}
            onChange={form.handleChange}
            onBlur={form.handleBlur}
          />
          {form.touched.email && form.errors.email && (
            <span className="error">{form.errors.email}</span>
          )}
        </div>
        
        <div>
          <label>Age:</label>
          <input
            type="number"
            name="age"
            value={form.values.age}
            onChange={form.handleChange}
            onBlur={form.handleBlur}
          />
          {form.touched.age && form.errors.age && (
            <span className="error">{form.errors.age}</span>
          )}
        </div>
        
        <button type="submit">Submit</button>
        <button type="button" onClick={form.resetForm}>Reset</button>
      </form>
    </div>
  );
}
```

### 2. 状态管理接口

#### Context API
```javascript
import React, { createContext, useContext, useReducer } from 'react';

// 创建Context
const UserContext = createContext();

// 初始状态
const initialState = {
  user: null,
  loading: false,
  error: null
};

// Action类型
const USER_ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_USER: 'SET_USER',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR'
};

// Reducer函数
function userReducer(state, action) {
  switch (action.type) {
    case USER_ACTIONS.SET_LOADING:
      return { ...state, loading: action.payload };
    case USER_ACTIONS.SET_USER:
      return { ...state, user: action.payload, loading: false };
    case USER_ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    case USER_ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    default:
      return state;
  }
}

// Context Provider
function UserProvider({ children }) {
  const [state, dispatch] = useReducer(userReducer, initialState);

  const actions = {
    setLoading: (loading) => dispatch({ type: USER_ACTIONS.SET_LOADING, payload: loading }),
    setUser: (user) => dispatch({ type: USER_ACTIONS.SET_USER, payload: user }),
    setError: (error) => dispatch({ type: USER_ACTIONS.SET_ERROR, payload: error }),
    clearError: () => dispatch({ type: USER_ACTIONS.CLEAR_ERROR })
  };

  const value = { state, actions };

  return (
    <UserContext.Provider value={value}>
      {children}
    </UserContext.Provider>
  );
}

// 自定义Hook使用Context
function useUser() {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
}

// 使用Context的组件
function UserProfile() {
  const { state, actions } = useUser();
  const { user, loading, error } = state;

  React.useEffect(() => {
    const fetchUser = async () => {
      actions.setLoading(true);
      try {
        const response = await fetch('/api/user');
        const userData = await response.json();
        actions.setUser(userData);
      } catch (err) {
        actions.setError(err.message);
      }
    };

    fetchUser();
  }, [actions]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user data</div>;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>Email: {user.email}</p>
    </div>
  );
}

// 应用入口
function App() {
  return (
    <UserProvider>
      <div className="App">
        <UserProfile />
      </div>
    </UserProvider>
  );
}
```

#### Redux集成
```javascript
import { createStore, combineReducers, applyMiddleware } from 'redux';
import { Provider, useDispatch, useSelector } from 'react-redux';
import thunk from 'redux-thunk';

// Action类型
const USER_ACTIONS = {
  FETCH_USER_REQUEST: 'FETCH_USER_REQUEST',
  FETCH_USER_SUCCESS: 'FETCH_USER_SUCCESS',
  FETCH_USER_FAILURE: 'FETCH_USER_FAILURE'
};

// Action创建函数
const fetchUserRequest = () => ({ type: USER_ACTIONS.FETCH_USER_REQUEST });
const fetchUserSuccess = (user) => ({ type: USER_ACTIONS.FETCH_USER_SUCCESS, payload: user });
const fetchUserFailure = (error) => ({ type: USER_ACTIONS.FETCH_USER_FAILURE, payload: error });

// 异步Action
const fetchUser = () => async (dispatch) => {
  dispatch(fetchUserRequest());
  try {
    const response = await fetch('/api/user');
    const user = await response.json();
    dispatch(fetchUserSuccess(user));
  } catch (error) {
    dispatch(fetchUserFailure(error.message));
  }
};

// Reducer
const userReducer = (state = { user: null, loading: false, error: null }, action) => {
  switch (action.type) {
    case USER_ACTIONS.FETCH_USER_REQUEST:
      return { ...state, loading: true, error: null };
    case USER_ACTIONS.FETCH_USER_SUCCESS:
      return { ...state, loading: false, user: action.payload };
    case USER_ACTIONS.FETCH_USER_FAILURE:
      return { ...state, loading: false, error: action.payload };
    default:
      return state;
  }
};

// Store配置
const rootReducer = combineReducers({
  user: userReducer
});

const store = createStore(rootReducer, applyMiddleware(thunk));

// React组件
function UserProfile() {
  const dispatch = useDispatch();
  const { user, loading, error } = useSelector(state => state.user);

  React.useEffect(() => {
    dispatch(fetchUser());
  }, [dispatch]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!user) return <div>No user data</div>;

  return (
    <div>
      <h2>{user.name}</h2>
      <p>Email: {user.email}</p>
    </div>
  );
}

// 应用入口
function App() {
  return (
    <Provider store={store}>
      <div className="App">
        <UserProfile />
      </div>
    </Provider>
  );
}
```

### 3. 路由接口

#### React Router
```javascript
import { BrowserRouter as Router, Routes, Route, Link, useParams, useNavigate } from 'react-router-dom';

// 基础路由配置
function App() {
  return (
    <Router>
      <nav>
        <Link to="/">Home</Link>
        <Link to="/about">About</Link>
        <Link to="/users">Users</Link>
      </nav>

      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />
        <Route path="/users" element={<Users />} />
        <Route path="/users/:userId" element={<UserDetail />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

function Home() {
  return <h1>Home Page</h1>;
}

function About() {
  return <h1>About Page</h1>;
}

function Users() {
  const [users, setUsers] = React.useState([]);

  React.useEffect(() => {
    fetch('/api/users')
      .then(response => response.json())
      .then(data => setUsers(data));
  }, []);

  return (
    <div>
      <h1>Users</h1>
      <ul>
        {users.map(user => (
          <li key={user.id}>
            <Link to={`/users/${user.id}`}>{user.name}</Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

function UserDetail() {
  const { userId } = useParams();
  const navigate = useNavigate();
  const [user, setUser] = React.useState(null);

  React.useEffect(() => {
    fetch(`/api/users/${userId}`)
      .then(response => response.json())
      .then(data => setUser(data));
  }, [userId]);

  const handleBack = () => {
    navigate('/users');
  };

  if (!user) return <div>Loading...</div>;

  return (
    <div>
      <button onClick={handleBack}>Back to Users</button>
      <h1>{user.name}</h1>
      <p>Email: {user.email}</p>
      <p>Role: {user.role}</p>
    </div>
  );
}

function NotFound() {
  return <h1>404 - Page Not Found</h1>;
}

// 嵌套路由
function AppWithNestedRoutes() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="dashboard" element={<Dashboard />}>
            <Route path="overview" element={<Overview />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          <Route path="profile" element={<Profile />} />
        </Route>
      </Routes>
    </Router>
  );
}

function Layout() {
  return (
    <div>
      <header>
        <nav>
          <Link to="/">Home</Link>
          <Link to="/dashboard">Dashboard</Link>
          <Link to="/profile">Profile</Link>
        </nav>
      </header>
      
      <main>
        <Outlet /> {/* 嵌套路由渲染位置 */}
      </main>
    </div>
  );
}

function Dashboard() {
  return (
    <div>
      <h1>Dashboard</h1>
      <nav>
        <Link to="overview">Overview</Link>
        <Link to="settings">Settings</Link>
      </nav>
      
      <Outlet /> {/* 嵌套子路由渲染位置 */}
    </div>
  );
}

function Overview() {
  return <h2>Overview</h2>;
}

function Settings() {
  return <h2>Settings</h2>;
}

function Profile() {
  return <h1>Profile</h1>;
}
```

### 4. 样式接口

#### CSS Modules
```javascript
// UserProfile.module.css
.container {
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 10px;
}

.title {
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
}

.info {
  font-size: 16px;
  color: #666;
}

.highlight {
  background-color: #ffff00;
  padding: 2px 4px;
}

// UserProfile.js
import styles from './UserProfile.module.css';

function UserProfile({ user }) {
  return (
    <div className={styles.container}>
      <h2 className={styles.title}>{user.name}</h2>
      <p className={styles.info}>
        Email: <span className={styles.highlight}>{user.email}</span>
      </p>
      <p className={styles.info}>Role: {user.role}</p>
    </div>
  );
}
```

#### Styled Components
```javascript
import styled, { keyframes, css } from 'styled-components';

// 基础样式组件
const Container = styled.div`
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  margin: 10px;
  background-color: ${props => props.theme.backgroundColor || '#fff'};
  
  &:hover {
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }
`;

const Title = styled.h2`
  font-size: 24px;
  color: #333;
  margin-bottom: 10px;
  
  ${props => props.primary && css`
    color: #007bff;
  `}
`;

// 动画
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const AnimatedContainer = styled(Container)`
  animation: ${fadeIn} 0.5s ease-in-out;
`;

// 主题
const theme = {
  light: {
    backgroundColor: '#fff',
    textColor: '#333'
  },
  dark: {
    backgroundColor: '#333',
    textColor: '#fff'
  }
};

// 主题Provider
import { ThemeProvider } from 'styled-components';

function ThemedApp() {
  const [currentTheme, setCurrentTheme] = React.useState('light');

  return (
    <ThemeProvider theme={theme[currentTheme]}>
      <div>
        <button onClick={() => setCurrentTheme(
          currentTheme === 'light' ? 'dark' : 'light'
        )}>
          Toggle Theme
        </button>
        
        <UserProfile user={{ name: 'John Doe', email: 'john@example.com' }} />
      </div>
    </ThemeProvider>
  );
}

// 使用样式组件
function UserProfile({ user }) {
  return (
    <AnimatedContainer>
      <Title primary>{user.name}</Title>
      <p>Email: {user.email}</p>
    </AnimatedContainer>
  );
}
```

## 数据流分析

### 1. 组件渲染流程
```
状态/Props变化 → 调用render() → 生成虚拟DOM → Diff算法比较 → 更新真实DOM
```

### 2. 事件处理流程
```
用户交互 → 事件触发 → 调用事件处理函数 → 更新状态 → 触发重新渲染
```

### 3. 生命周期流程（类组件）
```
挂载阶段: constructor → render → componentDidMount
更新阶段: shouldComponentUpdate → render → componentDidUpdate
卸载阶段: componentWillUnmount
```

### 4. Hooks执行流程
```
函数组件调用 → 执行Hooks → 返回JSX → 浏览器渲染 → 等待下一次更新
```

## 关键代码实现细节

### 1. React元素创建
```javascript
// ReactElement.js
const RESERVED_PROPS = {
  key: true,
  ref: true,
  __self: true,
  __source: true,
};

function ReactElement(type, key, ref, self, source, owner, props) {
  const element = {
    // 标识这是一个React元素
    $$typeof: REACT_ELEMENT_TYPE,
    
    // 内置属性
    type: type,
    key: key,
    ref: ref,
    props: props,
    
    // 记录创建此元素的组件
    _owner: owner,
  };

  if (__DEV__) {
    // 开发环境下的额外属性
    element._store = {};
    Object.defineProperty(element._store, 'validated', {
      configurable: false,
      enumerable: false,
      writable: true,
      value: false,
    });
    
    element._self = self;
    element._source = source;
  }

  return element;
}

function createElement(type, config, children) {
  let propName;

  // 保留的属性
  const props = {};

  let key = null;
  let ref = null;
  let self = null;
  let source = null;