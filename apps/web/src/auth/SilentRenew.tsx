import { useEffect } from 'react';
import { useAuth } from 'react-oidc-context';

const SilentRenew = () => {
  const auth = useAuth();

  useEffect(() => {
    auth.startSilentRenew();
  }, [auth]);

  return null;
};

export default SilentRenew;
