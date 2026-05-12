import React from 'react';
import {render, fireEvent, waitFor} from '@testing-library/react-native';
import LoginScreen from '../src/screens/auth/LoginScreen';

const mockLogin = jest.fn();

jest.mock('../src/store/authStore', () => ({
  useAuthStore: () => ({
    login: mockLogin,
  }),
}));

describe('LoginScreen', () => {
  beforeEach(() => {
    mockLogin.mockClear();
  });

  it('renders email and password inputs', () => {
    const {getByTestId} = render(<LoginScreen />);
    expect(getByTestId('email-input')).toBeTruthy();
    expect(getByTestId('password-input')).toBeTruthy();
  });

  it('renders login button', () => {
    const {getByTestId} = render(<LoginScreen />);
    expect(getByTestId('login-btn')).toBeTruthy();
  });

  it('renders demo account buttons', () => {
    const {getByTestId} = render(<LoginScreen />);
    expect(getByTestId('demo-admin')).toBeTruthy();
    expect(getByTestId('demo-manager')).toBeTruthy();
  });

  it('fills email on demo button press', () => {
    const {getByTestId} = render(<LoginScreen />);
    fireEvent.press(getByTestId('demo-admin'));
    const emailInput = getByTestId('email-input');
    expect(emailInput.props.value).toBe('admin@csplatform.local');
  });

  it('calls login on button press with values', async () => {
    mockLogin.mockResolvedValue(undefined);
    const {getByTestId} = render(<LoginScreen />);

    fireEvent.changeText(getByTestId('email-input'), 'agent1@csplatform.local');
    fireEvent.changeText(getByTestId('password-input'), 'Admin@123');
    fireEvent.press(getByTestId('login-btn'));

    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith(
        'agent1@csplatform.local',
        'Admin@123',
        undefined,
      );
    });
  });
});
