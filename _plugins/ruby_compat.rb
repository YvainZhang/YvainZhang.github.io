# Compatibility shim for older Jekyll/Liquid on modern Ruby.
unless "".respond_to?(:tainted?)
  class Object
    def tainted?
      false
    end
  end
end
